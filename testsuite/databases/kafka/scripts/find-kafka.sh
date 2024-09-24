#!/bin/sh

MIN_JAVA_VERSION="8"
MIN_KAFKA_VERSION_MAJOR="3"
MIN_KAFKA_VERSION_MINOR="3"

check_java() {
    if [ -n "$JAVA_HOME" ] && [ -x "$JAVA_HOME/bin/java" ];  then
        _java="$JAVA_HOME/bin/java"
        echo "Found java executable in JAVA_HOME: $_java"
    elif type java; then
        echo "Found java executable in PATH"
        _java=java
    else
        echo "No java found"
        return 1
    fi

    if [ "$_java" ]; then
        version=$("$_java" -version 2>&1 | grep -oP 'version "?(1\.)?\K\d+')
        echo "Current Java version is $version"
        if [ "$version" -ge $MIN_JAVA_VERSION ]; then
            return 0
        else
            echo "Java version must be at least $MIN_JAVA_VERSION"
            return 1
        fi
    fi
}

find_kafka() {
    if [ "x$KAFKA_HOME" = "x" ]; then
        echo "
    KAFKA_HOME env is not specified!!!.
    Please download Kafka from https://kafka.apache.org/downloads,
    unpack the archive and place path to it in KAFKA_HOME"
        return 1
    fi
    return 0
}

check_kafka() {
    kafka_bin_dir="$KAFKA_HOME/bin"
    echo "Kafka bin directory: $kafka_bin_dir"
    cd "$kafka_bin_dir"

    kafka_version=$(./kafka-run-class.sh org.apache.kafka.tools.TopicCommand --version)
    echo "Found Kafka version $kafka_version"

    major_version=$(echo $kafka_version | cut -d'.' -f 1)
    minor_version=$(echo $kafka_version | cut -d'.' -f 2)
    if [ "$major_version" -gt $MIN_KAFKA_VERSION_MAJOR ]; then
        return 0
    elif [ \( "$major_version" -eq $MIN_KAFKA_VERSION_MAJOR \) -o \( $minor_version -ge $MIN_KAFKA_VERSION_MINOR \) ]; then
        return 0
    else
        echo "Minimum required Kafka version is $MIN_KAFKA_VERSION_MAJOR.$MIN_KAFKA_VERSION_MINOR"
        return 1
    fi
}

check_java || die "Java check failed"
find_kafka || die "Kafka is not found"
check_kafka || die "Kafka cannot be started"
