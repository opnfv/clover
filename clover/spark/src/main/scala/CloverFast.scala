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

object CloverFast {
  def main(args: Array[String]) {
    val sp = SparkSession.builder.appName("Clover Fast")
                         .getOrCreate()
    sp.stop()

    val CassandraConnect = "cassandra.clover-system"
    val RedisConnect = "redis.default"

    // Cassandra, Redis, Spark Context
    val scch = "spark.cassandra.connection.host"
    val conf = new SparkConf(true).set(scch, CassandraConnect)
    val redis = new RedisClient(RedisConnect, 6379)
    val sc = new SparkContext(conf)

    for(  x <- 1 to 10000 ) {

        try {
            val spans = sc.cassandraTable("visibility", "spans")
                          .select("spanid").cassandraCount()
            redis.set("span_count", spans)

            val traces = sc.cassandraTable("visibility", "traces")
                           .select("traceid").cassandraCount()
            redis.set("trace_count", traces)

            val metrics = sc.cassandraTable("visibility", "metrics")
                            .select("monitor_time").cassandraCount()
            redis.set("metric_count", metrics)

        }
        catch {
            case unknown : Throwable => println("System counts exception: "
                                                + unknown)
        }

    }

  }
}
