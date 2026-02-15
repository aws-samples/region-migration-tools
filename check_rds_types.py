"""
Compare RDS instance classes and engine versions between two regions.

This script checks if RDS instances running in the source region are available
in the target region, including both instance classes and engine versions.
"""
import sys
import boto3
from utils.aws_clients import aws_client_factory


def get_in_use_rds_classes_and_ids(region):
    rds = aws_client_factory.get_rds_client(region)
    paginator = rds.get_paginator("describe_db_instances")

    instance_classes_and_ids = {}
    instance_engines_and_versions = {}

    for page in paginator.paginate():
        for db_instance in page["DBInstances"]:
            class_ = db_instance["DBInstanceClass"]
            engine = db_instance["Engine"]
            engine_version = db_instance["EngineVersion"]
            if class_ in instance_classes_and_ids:
                instance_classes_and_ids[class_].append(
                    db_instance["DBInstanceIdentifier"]
                )
            else:
                instance_classes_and_ids[class_] = [db_instance["DBInstanceIdentifier"]]
                instance_engines_and_versions[class_] = (engine, engine_version)

    return instance_classes_and_ids, instance_engines_and_versions


def compare_rds_classes(region1, region2, verbose=False):
    """
    Compare RDS instance classes and engine versions between two regions
    
    Args:
        region1: Source region with RDS instances
        region2: Target region to check availability
        verbose: Enable verbose output
    """
    if verbose:
        print(f"Checking RDS instances in {region1} vs availability in {region2}")
        print("Fetching RDS instances from source region...")
    
    (
        classes_and_ids_region1,
        engines_and_versions_region1,
    ) = get_in_use_rds_classes_and_ids(region1)

    if not engines_and_versions_region1:
        print(f"No RDS instances found in {region1}")
        return
    
    if verbose:
        print(f"Found {len(engines_and_versions_region1)} RDS instance classes in {region1}")
        print("Checking availability in target region...")

    not_in_region2 = {}

    for class_, (engine, version) in engines_and_versions_region1.items():
        classes_region2 = get_rds_classes(region2, engine)
        engine_versions_region2 = get_rds_engine_versions(region2, engine)

        class_available = class_ in classes_region2
        version_available = version in engine_versions_region2

        if not class_available or not version_available:
            not_in_region2[class_] = (
                classes_and_ids_region1[class_],
                version,
                class_available,
                version_available,
            )

    if not not_in_region2:
        print(f"✓ All RDS instance classes and engine versions from {region1} are available in {region2}")
        return

    print(
        f"RDS Instance Classes and/or Engine Versions in use in {region1} not available in {region2}:"
    )
    for class_, (
        ids,
        version,
        class_available,
        version_available,
    ) in not_in_region2.items():
        if not class_available and not version_available:
            print(
                f"  Class: {class_}, Engine Version: {version}, Instance IDs: {ids} - both class and version not available"
            )
        elif not class_available:
            print(
                f"  Class: {class_}, Engine Version: {version}, Instance IDs: {ids} - class not available"
            )
        else:
            print(
                f"  Class: {class_}, Engine Version: {version}, Instance IDs: {ids} - engine version not available"
            )


def get_rds_classes(region, engine):
    rds = aws_client_factory.get_rds_client(region)
    paginator = rds.get_paginator("describe_orderable_db_instance_options")

    instance_classes = set()

    for page in paginator.paginate(Engine=engine):
        for instance_class in page["OrderableDBInstanceOptions"]:
            instance_classes.add(instance_class["DBInstanceClass"])

    return instance_classes


def get_rds_engine_versions(region, engine):
    rds = aws_client_factory.get_rds_client(region)
    paginator = rds.get_paginator("describe_orderable_db_instance_options")

    engine_versions = set()

    for page in paginator.paginate(Engine=engine):
        for option in page["OrderableDBInstanceOptions"]:
            engine_versions.add(option["EngineVersion"])

    return engine_versions


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python check_rds_types.py <region1> <region2>")
        sys.exit(1)

    REGION1 = sys.argv[1]
    REGION2 = sys.argv[2]

    compare_rds_classes(REGION1, REGION2)
