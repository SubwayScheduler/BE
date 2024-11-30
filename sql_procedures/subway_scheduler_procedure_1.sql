DELIMITER $$

CREATE PROCEDURE GetRoundTripHistogram(IN lineId INT)
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
                ID AS station_ID,
                name
            FROM
                station
            WHERE
                line_ID = lineId
        ),
        eta_adjusted AS (
            SELECT
                eta.station_ID,
                eta.ET,
                LEAD(eta.ET) OVER (
                    ORDER BY
                        eta.station_ID ASC
                ) AS next_ET
            FROM
                eta
        ),
        base_data AS (
            SELECT
                ROW_NUMBER() OVER (
                    ORDER BY
                        platform.bound_to DESC,
                        CASE
                            WHEN platform.bound_to = 1 THEN station.ID
                            WHEN platform.bound_to = 0 THEN - station.ID
                        END
                ) AS seq_number,
                station.ID,
                platform.bound_to,
                station.name,
                COALESCE(
                    CASE
                        WHEN platform.bound_to = 1 THEN eta.ET
                        WHEN platform.bound_to = 0 THEN eta_adjusted.next_ET
                    END,
                    '00:00:00'
                ) AS ET
            FROM
                platform
                INNER JOIN station ON platform.station_ID = station.ID
                INNER JOIN selected_stations ON station.ID = selected_stations.station_ID
                LEFT JOIN eta ON station.ID = eta.station_ID
                LEFT JOIN eta_adjusted ON station.ID = eta_adjusted.station_ID
            WHERE
                NOT(
                    platform.bound_to = 1
                    AND station.ID = (
                        SELECT
                            MAX(ID)
                        FROM
                            station
                        WHERE
                            line_ID = lineId
                    )
                )
        ),
        cumulated_data AS (
            SELECT
                seq_number,
                ID,
                bound_to,
                name,
                ET,
                SUM(TIME_TO_SEC(ET)) OVER (
                    ORDER BY
                        seq_number
                ) AS cumulated_time_seconds
            FROM
                base_data
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
                    ts.base_time,
                    SEC_TO_TIME(FLOOR(cd.cumulated_time_seconds / 1800) * 1800)
                ) AS time_slot
            FROM
                cumulated_data cd
                CROSS JOIN time_slots ts
        ),
        congestion_summary AS (
            SELECT
                platform_station_ID,
                platform_bound_to,
                time_slot,
                SUM(congest_status) AS total_congestion
            FROM
                congestion
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
            
            -- 05:00의 초기값 추가
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
        ROUND(h.total_congestion / SUM(h.total_congestion) OVER (), 4) AS pdf_value,
        ROUND(
            (
                COALESCE(
                    SUM(h.total_congestion) OVER (ORDER BY h.slot_id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),
                    0
                )
                + (h.total_congestion * 0.5)
            ) / SUM(h.total_congestion) OVER (), 
            4
        ) AS cdf_value
    FROM 
        base_histogram h
    ORDER BY 
        h.slot_id;
END $$

DELIMITER ;