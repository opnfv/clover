// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

name := "Clover Spark"

version := "1.0"

scalaVersion := "2.11.6"

libraryDependencies += "org.apache.spark" %% "spark-sql" % "2.3.2"
libraryDependencies += "datastax" % "spark-cassandra-connector" % "2.3.0-s_2.11"

libraryDependencies ++= Seq(
   "net.debasishg" %% "redisclient" % "3.7"
)
