DELIMITER $$

CREATE PROCEDURE GetRoundTripHistogram(IN lineId INT)
BEGIN
    WITH RECURSIVE
        time_slots AS (
            SELECT
                '05:30:00' AS base_time
            UNION ALL
            SELECT
                ADDTIME(base_time, '00:30:00') AS base_time
            FROM
                time_slots
            WHERE
                base_time < '24:30:00'
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
                a.start_time,
                SUM(COALESCE(cs.total_congestion, 0)) AS total_congestion
            FROM
                all_arrival_data a
                LEFT JOIN congestion_summary cs ON cs.platform_station_ID = a.ID
                AND cs.platform_bound_to = a.bound_to
                AND cs.time_slot = a.time_slot
            GROUP BY
                a.start_time
        )
    SELECT 
        h.start_time,
        h.total_congestion,
        ROUND(h.total_congestion / SUM(h.total_congestion) OVER (), 4) AS pdf_value,
        ROUND(SUM(h.total_congestion) OVER (ORDER BY h.start_time) 
              / SUM(h.total_congestion) OVER (), 4) AS cdf_value
    FROM 
        base_histogram h
    ORDER BY 
        h.start_time;
END $$

DELIMITER ;