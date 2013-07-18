import re

def parse_sns_arn(arn):
    """
    Matches the provided ARN against a regex and returns a dictionary with the following values:
        - region: The topic region
        - account_id: The account id of the topic
        - topic_id: The unique id of the topic in the region

    :param arn: he full ARN of the SNS topic
    :type arn: str
    :return: A dictionary with region, account_id and topic_id
    :rtype: dict
    :raise ValueError: If the specified ARN is invalid
    """
    regex = re.compile(r"arn:aws:sns:(?P<region>[a-z0-9-]+):(?P<account_id>[0-9]+):(?P<sns_id>.+)")
    r = regex.search(arn)
    if not r:
        raise ValueError("Argument '%s' doesn't appear to be a valid Amazon SNS ARN", arn)

    return r.groupdict()