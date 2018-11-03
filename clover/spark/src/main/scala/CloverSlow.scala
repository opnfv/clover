// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0


import org.apache.spark.sql.SparkSession
import com.datastax.spark.connector._
import org.apache.spark.sql.cassandra._


import org.apache.spark.SparkContext
import org.apache.spark.SparkConf

import com.redis._

object CloverSlow {
  def main(args: Array[String]) {
    val sp = SparkSession.builder.appName("Clover Slow").getOrCreate()
    sp.stop()

    val CassandraConnect = "cassandra.clover-system"
    val RedisConnect = "redis.default"


    // Enable/disable various analytics
    val distinct_url_service = false
    val response_times = true

    // Cassandra, Redis, Spark Context
    val scch = "spark.cassandra.connection.host"
    val conf = new SparkConf(true).set(scch, CassandraConnect)
    val redis = new RedisClient(RedisConnect, 6379)
    val sc = new SparkContext(conf)

    val spark = SparkSession
    .builder()
    .appName("Clover Visibility Stats")
    .config("spark.cassandra.connection.host", CassandraConnect)
    .config("spark.cassandra.connection.port", "9042")
    .getOrCreate()

    spark
    .read.cassandraFormat("spans", "visibility")
    .load()
    .createOrReplaceTempView("curspans")

    for(  x <- 1 to 500 ) {

        val services = redis.smembers("visibility_services")

        if (distinct_url_service) {
            // Get number of distinct URLs per service (node_id)
            for (s <- services.get) {
                val service = s.get
                val perurl = spark.sql(
                s"""
                    |SELECT node_id,count(distinct http_url)
                    |as urls,collect_set(http_url) as values
                    |FROM curspans
                    |WHERE node_id LIKE '%$service%'
                    |GROUP BY node_id
                """.stripMargin)
                for ((row) <- perurl.collect) {
                    println(row)
                    val node_id = row.get(0)
                    val url_count  = row.get(1)
                    val url_distinct  = row.getList(2).toString
                    redis.hmset(service, Map("node_id" -> node_id,
                                             "url_count" -> url_count,
                                             "url_distinct" -> url_distinct))
                }
            }
        }

        if (response_times) {
            try {
                for (s <- services.get) {
                    val service = s.get.replace('_', '-')
                    val service_rt = spark.sql(
                    s"""
                        |SELECT avg(duration),min(duration),max(duration)
                        |FROM curspans
                        |WHERE node_id LIKE '%$service%'
                        |AND upstream_cluster LIKE '%inbound%'
                    """.stripMargin)
                    if (service_rt.count > 0) {
                        val avg_rt = service_rt.first.getDouble(0) / 1000.0
                        val min_rt = service_rt.first.getInt(1) / 1000.0
                        val max_rt = service_rt.first.getInt(2) / 1000.0
                        redis.hmset(service, Map("avg_rt" -> f"$avg_rt%1.2f",
                                                 "min_rt" -> f"$min_rt%1.2f",
                                                 "max_rt" -> f"$max_rt%1.2f"))
                    } else {
                        redis.hmset(service, Map("avg_rt" -> "NA",
                                                 "min_rt" -> "NA",
                                                 "max_rt" -> "NA"))
                    }
                }
            } catch {
                case unknown : Throwable => println("RT exception: "
                                                    + unknown)
                //unknown.printStackTrace
            }
        }

        // Per URL counts all nodes
        val urlcount = spark.sql(
        s"""
            |SELECT http_url,count(http_url) as urls FROM curspans
            |GROUP BY http_url
        """.stripMargin)
        redis.del("span_urls")
        redis.del("span_urls_z")
        for ((row) <- urlcount.collect) {
            redis.sadd("span_urls", row.get(0))
            redis.zadd("span_urls_z", row.getLong(1).toDouble, row.get(0))
        }

        // User-Agents all nodes
        val uacount = spark.sql(
        s"""
            |SELECT user_agent,count(user_agent) as ua FROM curspans
            |GROUP BY user_agent
        """.stripMargin)
        redis.del("span_user_agent")
        redis.del("span_user_agent_z")
        for ((row) <- uacount.collect) {
            redis.sadd("span_user_agent", row.get(0))
            redis.zadd("span_user_agent_z", row.getLong(1).toDouble,
                       row.get(0))
        }

        // Node ids all nodes
        val nodecount = spark.sql(
        s"""
            |SELECT node_id,count(node_id) as node FROM curspans
            |GROUP BY node_id
        """.stripMargin)
        redis.del("span_node_id")
        redis.del("span_node_id_z")
        for ((row) <- nodecount.collect) {
            redis.sadd("span_node_id", row.get(0))
            redis.zadd("span_node_id_z", row.getLong(1).toDouble, row.get(0))
        }

        // Per URL/status codes all nodes
        val statuscount = spark.sql(
        s"""
            |SELECT http_url,status_code,count(status_code) as urls
            |FROM curspans
            |GROUP BY http_url,status_code
        """.stripMargin)
        redis.del("span_status_codes_z")
        for ((row) <- statuscount.collect) {
            val key_url_code = row.get(1) + ", " + row.get(0)
            redis.zadd("span_status_codes_z", row.getLong(2).toDouble,
                       key_url_code)
        }

        // Per Service/URL counts
        val node_url_count = spark.sql(
        s"""
            |SELECT node_id,http_url,count(http_url) as urls
            |FROM curspans
            |GROUP BY node_id,http_url
        """.stripMargin)
        redis.del("span_node_url_z")
        for ((row) <- node_url_count.collect) {
            val key_node_url = row.get(0) + ", " + row.get(1)
            redis.zadd("span_node_url_z", row.getLong(2).toDouble,
                       key_node_url)
        }

        // Distinct span fields
        val distinct_keys = List("operation_name", "upstream_cluster",
                                 "status_code")
        for (field <- distinct_keys) {
            val distinct_span = spark.sql(
            s"""
                |SELECT $field FROM curspans
                |GROUP BY $field
            """.stripMargin)
            val dk = "span_" + field
            redis.del(dk)
            for ((row) <- distinct_span.collect) {
                redis.sadd(dk, row.get(0))
            }
        }

        // Metrics, per service
        spark
        .read.cassandraFormat("metrics", "visibility")
        .load()
        .createOrReplaceTempView("curmetrics")

        val metric_prefixes = redis.smembers("metric_prefixes")
        val metric_suffixes = redis.smembers("metric_suffixes")

        try {
            for (s <- services.get) {
                //val service = s.get.replace('_', '-')
                val service = s.get
                for (m_prefix <- metric_prefixes.get) {
                    val mp = m_prefix.get
                    for (m_suffix <- metric_suffixes.get) {
                        val ms = m_suffix.get
                        val metric_result = spark.sql(
                        s"""
                            |SELECT m_value FROM curmetrics
                            |WHERE m_name = '$mp$service$ms'
                            |ORDER BY m_time DESC LIMIT 100
                        """.stripMargin)
                        val metric_key = "metrics_" + mp + service + ms
                        redis.del(metric_key)
                        for ((row) <- metric_result.collect) {
                            redis.lpush(metric_key, row.get(0))
                        }
                    }
                }
            }
        } catch {
            case unknown : Throwable => println("Metrics exception: "
                                                + unknown)
            // unknown.printStackTrace
        }
    }

  }
}
