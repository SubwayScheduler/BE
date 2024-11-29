DELIMITER $$

CREATE PROCEDURE GetCircularHistogram(IN lineId INT, IN boundTo INT)
BEGIN
    WITH RECURSIVE
        time_slots AS (
            SELECT base_time, slot_id
            FROM (
                -- 05:30 ~ 23:30
                WITH RECURSIVE regular_slots AS (
                    SELECT '05:30:00' AS base_time, 1 AS slot_id
                    UNION ALL
                    SELECT ADDTIME(base_time, '00:30:00'), slot_id + 1
                    FROM regular_slots
                    WHERE base_time < '23:30:00'
                )
                SELECT base_time, slot_id FROM regular_slots
                
                UNION ALL
                
                -- 00:00 ~ 00:30
                SELECT base_time, slot_id
                FROM (
                    SELECT '00:00:00' AS base_time, 38 AS slot_id
                    UNION ALL
                    SELECT '00:30:00', 39
                ) AS midnight_slots
            ) AS all_slots
        ),
        selected_stations AS (
            SELECT
                station.ID AS station_ID,
                station.name,
                line.route_shape
            FROM
                station
                INNER JOIN line ON station.line_ID = line.ID
            WHERE
                line.ID = lineId
        ),
        eta_adjusted AS (
            SELECT
                eta.station_ID,
                eta.ET,
                LEAD(eta.ET) OVER (
                    ORDER BY
                        CASE
                            WHEN boundTo = 1 THEN eta.station_ID
                            WHEN boundTo = 0 THEN - eta.station_ID
                        END
                ) AS next_ET
            FROM
                eta
        ),
        base_data AS (
            SELECT
                ROW_NUMBER() OVER (
                    ORDER BY
                        CASE
                            WHEN boundTo = 1 THEN station.ID
                            WHEN boundTo = 0 THEN - station.ID
                        END
                ) AS seq_number,
                station.ID,
                boundTo AS bound_to,
                station.name,
                ss.route_shape,
                COALESCE(
                    CASE
                        WHEN boundTo = 1 THEN eta.ET
                        WHEN boundTo = 0 THEN eta_adjusted.next_ET
                    END,
                    '00:00:00'
                ) AS ET
            FROM
                station
                INNER JOIN selected_stations ss ON station.ID = ss.station_ID
                LEFT JOIN eta ON station.ID = eta.station_ID
                LEFT JOIN eta_adjusted ON station.ID = eta_adjusted.station_ID
            WHERE
                station.line_ID = lineId
        ),
        cumulated_data AS (
            SELECT
                bd.seq_number,
                bd.ID,
                bd.bound_to,
                bd.name,
                bd.ET,
                SUM(TIME_TO_SEC(bd.ET)) OVER (
                    ORDER BY
                        bd.seq_number
                ) AS cumulated_time_seconds
            FROM
                base_data bd
        ),
        all_arrival_data AS (
            SELECT
                cd.seq_number,
                cd.ID,
                cd.bound_to,
                cd.name,
                cd.ET,
                SEC_TO_TIME(cd.cumulated_time_seconds) AS cumulated_time,
                ts.base_time AS start_time,
                ADDTIME(
                    ts.base_time,
                    SEC_TO_TIME(cd.cumulated_time_seconds)
                ) AS arrival_time,
                ADDTIME(
                    '00:00:00',
                    SEC_TO_TIME(
                        FLOOR(
                            TIME_TO_SEC(
                                ADDTIME(
                                    ts.base_time,
                                    SEC_TO_TIME(cd.cumulated_time_seconds)
                                )
                            ) / 1800
                        ) * 1800
                    )
                ) AS time_slot
            FROM
                cumulated_data cd
                CROSS JOIN time_slots ts
            WHERE
                ADDTIME(
                    ts.base_time,
                    SEC_TO_TIME(cd.cumulated_time_seconds)
                ) < '24:00:00'
        ),
        congestion_summary AS (
            SELECT
                platform_station_ID,
                platform_bound_to,
                time_slot,
                SUM(congest_status) AS total_congestion
            FROM
                congestion
            WHERE
                platform_bound_to = boundTo
            GROUP BY
                platform_station_ID,
                platform_bound_to,
                time_slot
        ),
        base_histogram AS (
            SELECT
                ADDTIME(a.start_time, '00:15:00') as start_time,
                MIN(ts.slot_id) + 1 as slot_id,
                SUM(COALESCE(cs.total_congestion, 0)) AS total_congestion
            FROM
                all_arrival_data a
                LEFT JOIN congestion_summary cs ON cs.platform_station_ID = a.ID
                AND cs.platform_bound_to = a.bound_to
                AND cs.time_slot = a.time_slot
                LEFT JOIN time_slots ts ON ts.base_time = a.start_time
            GROUP BY
                a.start_time
            
            UNION ALL
            
            -- 05:15의 초기값 추가
            SELECT 
                '05:15:00' as start_time,
                0 as slot_id,
                0 as total_congestion

            UNION ALL

            -- 01:15의 초기값 추가
            SELECT 
                '01:15:00' as start_time,
                40 as slot_id,
                0 as total_congestion
        )
    SELECT 
        h.start_time,
        h.total_congestion,
        ROUND(h.total_congestion / NULLIF(SUM(h.total_congestion) OVER (), 0), 4) AS pdf_value,
        ROUND(
            (
                COALESCE(
                    SUM(h.total_congestion) OVER (ORDER BY h.slot_id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),
                    0
                )
                + (h.total_congestion * 0.5)
            ) / NULLIF(SUM(h.total_congestion) OVER (), 0), 
            4
        ) AS cdf_value
    FROM 
        base_histogram h
    ORDER BY 
        h.slot_id;
END $$

DELIMITER ;