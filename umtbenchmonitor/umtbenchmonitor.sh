#!/bin/sh

HLS_HOME="$(pwd)"
JAVA_OPT="-classpath "
for ext in $HLS_HOME/*.jar; do
	JAVA_OPT="$JAVA_OPT:$ext"
done
echo $JAVA_OPT

java $JAVA_OPT com.uvaca.monitor.MainProcess

