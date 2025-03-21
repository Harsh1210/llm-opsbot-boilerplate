from langchain_core.tools import tool
import boto3

# Initialize AWS EC2 Client
AWS_REGION = "ap-south-1"
ec2 = boto3.client("ec2", region_name=AWS_REGION)

# Store user responses across interactions
USER_SESSION = {}

@tool
def list_security_groups() -> str:
    """
    Lists all available security groups in the AWS region.
    
    Returns a formatted string with security group names and IDs.
    """
    security_groups = ec2.describe_security_groups()["SecurityGroups"]
    if not security_groups:
        return "❌ No security groups found."

    response = "\n".join([f"- {sg['GroupName']} (ID: {sg['GroupId']})" for sg in security_groups])
    return f"**Available Security Groups:**\n{response}"

@tool
def list_key_pairs() -> str:
    """
    Lists all available EC2 key pairs.

    Returns a formatted string with key pair names.
    """
    key_pairs = ec2.describe_key_pairs()["KeyPairs"]
    if not key_pairs:
        return "❌ No key pairs found. You may need to create one."

    response = "\n".join([f"- {kp['KeyName']}" for kp in key_pairs])
    return f"**Available Key Pairs:**\n{response}"

@tool
def list_volume_types() -> str:
    """
    Lists available EC2 volume types and their common use cases.

    Returns a formatted string with volume types.
    """
    volume_types = {
        "gp3": "General Purpose SSD (default)",
        "gp2": "Older General Purpose SSD",
        "io1": "Provisioned IOPS SSD (high performance)",
        "io2": "Provisioned IOPS SSD (high durability)",
        "st1": "Throughput Optimized HDD (for big data workloads)",
        "sc1": "Cold HDD (for infrequent access)",
        "standard": "Magnetic (legacy type)"
    }

    response = "\n".join([f"- **{vt}**: {desc}" for vt, desc in volume_types.items()])
    return f"**Available Volume Types:**\n{response}"

@tool
def create_instance(user_id: str, request: str) -> str:
    """
    Creates an EC2 instance in AWS. If required details are missing, asks the user for them.

    :param user_id: Unique ID of the user to track session progress.
    :param request: The natural language request from the user.
    :return: Response message (either asking for more details or confirmation of instance creation).
    """
    required_params = ["instance_type", "ami", "key_name", "security_group", "volume_type", "volume_size", "project", "owner", "name"]

    if user_id not in USER_SESSION:
        USER_SESSION[user_id] = {}

    # Extract known details from user request
    if "t2.micro" in request or "t3.medium" in request:
        USER_SESSION[user_id]["instance_type"] = "t2.micro" if "t2.micro" in request else "t3.medium"
    if "Ubuntu" in request:
        USER_SESSION[user_id]["ami"] = "ami-12345678"  # Example Ubuntu AMI
    if "Amazon Linux" in request:
        USER_SESSION[user_id]["ami"] = "ami-87654321"  # Example Amazon Linux AMI
    if "use my key" in request:
        USER_SESSION[user_id]["key_name"] = "my-key-pair"
    if "default security group" in request:
        USER_SESSION[user_id]["security_group"] = "default"
    if "gp3" in request or "io1" in request:
        USER_SESSION[user_id]["volume_type"] = "gp3" if "gp3" in request else "io1"
    if "20GB" in request or "50GB" in request:
        USER_SESSION[user_id]["volume_size"] = "20" if "20GB" in request else "50"
    
    # Extracting mandatory tag values
    if "Project:" in request:
        USER_SESSION[user_id]["project"] = request.split("Project:")[-1].strip().split()[0]
    if "Owner:" in request:
        USER_SESSION[user_id]["owner"] = request.split("Owner:")[-1].strip().split()[0]
    if "Name:" in request:
        USER_SESSION[user_id]["name"] = request.split("Name:")[-1].strip().split()[0]

    # Check which details are missing
    missing_params = [param for param in required_params if param not in USER_SESSION[user_id]]

    if missing_params:
        next_param = missing_params[0]
        follow_up_questions = {
            "instance_type": "What instance type would you like? (e.g., t2.micro, t3.medium)",
            "ami": "Which OS image do you want? (e.g., Ubuntu 22.04, Amazon Linux 2)?",
            "key_name": "Do you have a key pair? If not, do you want me to create one?",
            "security_group": "Which security group should I attach? (Use `/list_security_groups` to see options.)",
            "volume_type": "What storage type do you need? (Use `/list_volume_types` to see options.)",
            "volume_size": "What size should the storage be? (e.g., 20GB, 50GB)?",
            "project": "What is the project name for this instance?",
            "owner": "Who is the owner of this instance?",
            "name": "What should be the instance name?"
        }
        return follow_up_questions[next_param]

    # ✅ All details available, create instance
    try:
        response = ec2.run_instances(
            ImageId=USER_SESSION[user_id]["ami"],
            InstanceType=USER_SESSION[user_id]["instance_type"],
            KeyName=USER_SESSION[user_id]["key_name"],
            SecurityGroups=[USER_SESSION[user_id]["security_group"]],
            MinCount=1,
            MaxCount=1,
            BlockDeviceMappings=[
                {
                    "DeviceName": "/dev/xvda",
                    "Ebs": {
                        "VolumeSize": int(USER_SESSION[user_id]["volume_size"]),
                        "VolumeType": USER_SESSION[user_id]["volume_type"],
                    },
                }
            ],
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Project", "Value": USER_SESSION[user_id]["project"]},
                        {"Key": "Owner", "Value": USER_SESSION[user_id]["owner"]},
                        {"Key": "Name", "Value": USER_SESSION[user_id]["name"]},
                    ],
                }
            ],
        )

        instance_id = response["Instances"][0]["InstanceId"]
        del USER_SESSION[user_id]  # ✅ Clear session after successful creation

        return f"✅ Successfully launched EC2 instance `{USER_SESSION[user_id]['name']}` with ID `{instance_id}`."
    
    except Exception as e:
        return f"❌ Error launching instance: {str(e)}"

@tool
def list_instances(query: str = "") -> str:
    """List all EC2 instances with their state, Name, and IPs."""
    instances = ec2.describe_instances()
    response = []
    
    for reservation in instances["Reservations"]:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            state = instance["State"]["Name"]
            tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}
            name = tags.get("Name", "Unnamed")
            private_ip = instance.get("PrivateIpAddress", "N/A")
            public_ip = instance.get("PublicIpAddress", "N/A")

            response.append(f"🖥️ **{name}**  \nID: {instance_id}  \nState: {state}  \nPrivate IP: {private_ip}  \nPublic IP: {public_ip}\n")

    if not response:
        return "No instances found."

    return "\n".join(response)

@tool
def start_instance(identifier: str) -> str:
    """
    Starts an EC2 instance using Name, IP, or Instance ID.
    """
    instance_id = get_instance_id(identifier)
    if not instance_id:
        return f"⚠️ No instance found with identifier: {identifier}"

    ec2.start_instances(InstanceIds=[instance_id])
    return f"✅ Instance {identifier} (ID: {instance_id}) is starting."

@tool
def stop_instance(identifier: str) -> str:
    """
    Stops an EC2 instance using Name, IP, or Instance ID.
    """
    instance_id = get_instance_id(identifier)
    if not instance_id:
        return f"⚠️ No instance found with identifier: {identifier}"

    ec2.stop_instances(InstanceIds=[instance_id])
    return f"⛔ Instance {identifier} (ID: {instance_id}) is stopping."

@tool
def describe_instance(identifier: str) -> str:
    """
    Retrieves detailed information about an EC2 instance using its identifier.
    
    The identifier can be an Instance ID, private IP, public IP, or the value of the 'Name' tag.
    
    Returns a formatted string with the instance details, including state, storage, and instance type.
    """
    instance_id = get_instance_id(identifier)
    if not instance_id:
        return f"❌ No instance found with identifier '{identifier}'. Please check and try again."

    response = ec2.describe_instances(InstanceIds=[instance_id])
    
    if not response["Reservations"]:
        return f"❌ No details found for instance '{identifier}'."

    instance = response["Reservations"][0]["Instances"][0]

    # ✅ Extract attached EBS volumes
    volumes = instance.get("BlockDeviceMappings", [])
    storage_details = "\n".join(
        [
            f"  - Volume ID: {vol['Ebs']['VolumeId']} (Device: {vol['DeviceName']})"
            for vol in volumes if "Ebs" in vol
        ]
    ) if volumes else "No attached volumes"

    return (
        f"**Instance Details**\n"
        f"- **Name:** {identifier}\n"
        f"- **Instance ID:** {instance['InstanceId']}\n"
        f"- **State:** {instance['State']['Name']}\n"
        f"- **Instance Type:** {instance['InstanceType']}\n"
        f"- **Private IP:** {instance.get('PrivateIpAddress', 'N/A')}\n"
        f"- **Public IP:** {instance.get('PublicIpAddress', 'N/A')}\n"
        f"- **Launch Time:** {instance['LaunchTime']}\n"
        f"- **Security Groups:** {[sg['GroupName'] for sg in instance.get('SecurityGroups', [])]}\n"
        f"- **Attached Storage:**\n{storage_details}\n"
        f"- **Tags:** { {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])} }\n"
    )

def get_instance_id(identifier: str) -> str:
    """
    Finds an EC2 instance ID based on Name tag, Public IP, Private IP, or given Instance ID.
    """
    # Check if identifier is an Instance ID directly
    if identifier.startswith("i-"):
        return identifier

    # Fetch all instances
    instances = ec2.describe_instances()
    
    for reservation in instances["Reservations"]:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}
            private_ip = instance.get("PrivateIpAddress", "")
            public_ip = instance.get("PublicIpAddress", "")
            name = tags.get("Name", "")

            # Match identifier with Name, IPs, or Instance ID
            if identifier in [name, private_ip, public_ip, instance_id]:
                return instance_id
    
    return None  # Return None if no match is found