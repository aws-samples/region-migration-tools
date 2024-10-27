import requests
import boto3
import os
import re
import uuid
from datetime import datetime
import zlib
import json

region = os.environ["AWS_REGION"]
log_table = os.environ["LOGGING_TABLE"]
cache_table = os.environ["CACHE_TABLE"]

account_client = boto3.client("account")
dynamo_client = boto3.resource("dynamodb", region_name=region)
logging_table = dynamo_client.Table(log_table)
caching_table = dynamo_client.Table(cache_table)
spinner_image = "<img alt='spinner' style='margin-left: 20px; margin-bottom: -10px; width:30px; height:30px; display: none;' src='data:image/gif;base64,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'>"
download_image = "<img alt='download' style='margin-bottom: -5px; width: 20px; height: 20px;' src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACQAAAAmCAMAAACbFsmhAAAAe1BMVEX////+/v6Kior9/f1oaGlISEn7+/tqamooKClwcHC+vr/Kysp2dncsLS2fn6A4OTmYmZkxMTEzMzQ6Ojq5ublFRUUbHBwiIiNHR0js7Ow2Njerq6uQkZG+vr4XFxgyMjN4eHltbW0jJCQUFBU+Pj8VFRYmJidmZmf8/PxT0CVlAAAAwUlEQVR42u3QBVLFMBCA4aR51uJajdve/4JoYJmyuMs/VvmibJaorK0EezyxdG75FILgfYB/9AbEtwSFOL9rjk/WcB9BXQOa5ug0ZZgjyJvNAm7R9k6MRSGCnKLa2y3m+r2oG1S+4UyoEOEXQhWEhlKrS7RCQ6p+8H7o0ZCqa71vOzSkUtH7qNCQyl+FhlZPmaKeMPQdEmpxcLhG85DabwR7Ms7ZV8efEZNT9USTZEa7J9KGWeefyNnnzTQa+0RmPAeEez7JHkVFbAAAAABJRU5ErkJggg=='>"
close_image = "<img alt='close' style='margin-top: 3px; width: 20px; height: 20px; cursor: pointer;' src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACQAAAAdCAMAAAD1qz7PAAAAk1BMVEXu7u6KioojJCQUFBVtbW0yMjN5eXp4eHmQkZG+vr6rq6u9vb3Kysq+vr8zMzQxMTGYmZksLS06OjobHBwcHB03Nzfa2tvU1NQzMzNPT1C5ubkaGxtFRUUeHh/c3NxjY2M4OTmfn6AgISHq6uoXFxhkZGVwcHAoKClxcXElJSYkJCVqampoaGlnZ2gVFRYmJidmZmdwYuDvAAAAn0lEQVR42mKgNuAhQo0UoPuxVmIYiKGgzBhmZjP9/8+FQTevUGpvc7TamVvnhFASsUNnOKobdJo4Ln4nZ1BVaJV1dd4f2EwN1uuuUKbAghto4ZlNXtDBVla+9nYKDmtluy3RKVE62NqsZ9PFER2lZazmk7GBjtoy7oADLcFhfxcoet2cRPoetYfA1QRcj2xLF7AcMnVDQDf/K/m2KeD4NxY4GjotRStlAAAAAElFTkSuQmCC'>"
up_image = "<img alt='expand' style='margin-top: 3px; width: 20px; height: 20px; cursor: pointer;' src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACQAAAAdCAMAAAD1qz7PAAAAhFBMVEXu7u5nZ2cmJicVFRYUFBW+vr8kJCVlZWbk5OQlJSYzMzTZ2tpiY2MxMTGYmZkaGxseHh9dXV6xsbE/P0DQ0NA3NzgcHB3V1dVGRkbKysphYWEgISG5ublFRUUbHBw6OjosLS12dnc4OTmfn6Dc3NwXFxgoKClwcHDKystqampoaGlmZmdEhBw3AAAAhElEQVR42uXSRRZDIQwFULTu7o7vf3117+vJn5MJdgnKMgvdok2oNSNluJBSJNIodVGUIdTFjIa19rtC+5lPxoN+521faM+zKWO9bummsKnyw6XqGzeF85Qrt0a9fGklaBJu4z7cEwvM2+/Mnx1stm+ZrIVnWa31W9s5+COWC0aHZxnECZwVCCU2GZDlAAAAAElFTkSuQmCC'>"
down_image = "<img alt='shrink' style='margin-top: 3px; width: 20px; height: 20px; cursor: pointer;' src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACQAAAAdCAMAAAD1qz7PAAAAgVBMVEXu7u5nZ2cmJicVFRYUFBW+vr8zMzQkJCVkZGXIyMjl5eXa2toxMTGYmZkaGxt2dncsLS1ubm4gISE6OjobHBwcHB03Nzjf399QUFBiY2Pd3d0eHh9FRUa5ublFRUUlJSZlZWbKysqfn6A4OTkXFxgoKClwcHDY2NhqampoaGlmZmd0dbhMAAAAg0lEQVR42u3KxQHCUBRE0XiCuzt8778/3C+yRTKbJ3O8L8/Ce5/J1Dx6K3V1xK124NM4Ke3lqtXDkMoFoVgtr2+ow8/i4z/88MebKiscDj0/G6o0K+3Woj+7MlSD4XZrBNeGajTWvX7zxlBF1aTbiWju1DY0VDRUNIgtJwZPpBJ7eZAN9RkH40qbDd8AAAAASUVORK5CYII='>"

def lambda_handler(event, context):
    """
    Takes two region names and compares the CFN specs between the two
    """
    today = datetime.today()
    region1 = "ap-southeast-2"
    region2 = "ap-southeast-4"
    preview_image = ""
    format = "html"
    if "queryStringParameters" in event and event["queryStringParameters"] != None:
        if "region1" in event["queryStringParameters"] and re.match(
            r"[a-zA-Z0-9\-]{9,14}", event["queryStringParameters"]["region1"]
        ):
            region1 = re.sub(
                r"[^a-zA-Z0-9\-]", "", event["queryStringParameters"]["region1"]
            ).lower()
        if "region2" in event["queryStringParameters"] and re.match(
            r"[a-zA-Z0-9\-]{9,14}", event["queryStringParameters"]["region2"]
        ):
            region2 = re.sub(
                r"[^a-zA-Z0-9\-]", "", event["queryStringParameters"]["region2"]
            ).lower()
        if (
            "format" in event["queryStringParameters"]
            and event["queryStringParameters"]["format"] == "csv"
        ):
            format = "csv"

    params = {
        "id": str(uuid.uuid4()),
        "date": str(datetime.timestamp(datetime.now())),
        "region1": region1,
        "region2": region2,
    }
    logging_table.put_item(TableName=log_table, Item=params)

    response = ""
    have_cached = {}
    today_resultname = region1 + "-" + region2 + "-{}".format(today.date())

    if (
        "queryStringParameters" in event
        and "ignoreCache" not in event["queryStringParameters"]
    ):
        have_cached = caching_table.get_item(Key={"id": today_resultname})

    if "Item" in have_cached:
        print("returning a cached response as already compared today")
        response = zlib.decompress(bytes(have_cached["Item"]["response"])).decode()
    else:
        (reg1_instances, reg2_instances, both_instances) = get_instance_types(
            region1, region2
        )
        (reg1_dbengines, reg2_dbengines, both_dbengines) = get_db_engines(
            region1, region2
        )
        (reg1_apis, reg2_apis, both_apis) = get_api_presence(region1, region2)

        regions = account_client.list_regions(
            MaxResults=50,
            RegionOptStatusContains=[
                "ENABLED",
                "ENABLING",
                "DISABLING",
                "DISABLED",
                "ENABLED_BY_DEFAULT",
            ],
        )
        region_dropdown_1 = "<select id='region1'>"
        region_dropdown_2 = "<select id='region2'>"
        regions["Regions"].append({"RegionName": "us-gov-east-1"})
        regions["Regions"].append({"RegionName": "us-gov-west-1"})
        regions["Regions"].append({"RegionName": "cn-north-1"})
        regions["Regions"].append({"RegionName": "cn-northwest-1"})
        region_dropdown_1_options = []
        region_dropdown_2_options = []
        for region_record in regions["Regions"]:
            region1_selected = (
                " selected" if region1 == region_record["RegionName"] else ""
            )
            region2_selected = (
                " selected" if region2 == region_record["RegionName"] else ""
            )
            sortable_name = get_nice_name(region_record["RegionName"], True)
            nice_name = (
                sortable_name.split(": ")[1] + ", " + sortable_name.split(": ")[0]
            )
            region_dropdown_1_options.append(
                "<option sort={} value='{}' {}>{}</option>".format(
                    sortable_name,
                    region_record["RegionName"],
                    region1_selected,
                    nice_name,
                )
            )
            region_dropdown_2_options.append(
                "<option sort={} value='{}' {}>{}</option>".format(
                    sortable_name,
                    region_record["RegionName"],
                    region2_selected,
                    nice_name,
                )
            )
        region_dropdown_1_options.sort()
        region_dropdown_2_options.sort()
        region_dropdown_1 += "".join(region_dropdown_1_options) + "</select>"
        region_dropdown_2 += "".join(region_dropdown_2_options) + "</select>"
        go_button = (
            "<script>\n"
            + "let regionQs = '?region1=' + document.getElementById('region1').value;\n"
            + "regionQs += '&region2=' + document.getElementById('region2').value;\n"
            + "function changeRegions(ignoreCache,download){ \n"
            + "  let url='/?region1=' + document.getElementById('region1').value;\n"
            + "  url += '&region2=' + document.getElementById('region2').value;\n"
            + "  document.getElementById('spinner').style.display = 'inline';\n"
            + "  if (ignoreCache) {\n"
            + "    url += '&ignoreCache=1';\n"
            + "  }\n"
            + "  if (download) {\n"
            + "    url += '&format=csv';\n"
            + "    document.getElementById('spinner').style.display = 'none';\n"
            + "  }\n"
            + "  console.log(url);\n"
            + "  location.replace(url);\n"
            + "}\n"
            + "function toggleVisibity(colour) {\n"
            + "  let legend = document.getElementById(`${colour}Legend`);\n"
            + "  legend.style.setProperty('text-decoration', legend.style.getPropertyValue('text-decoration') === 'none' ? 'line-through' : 'none');\n"
            + "  let links = document.querySelectorAll(`.${colour}Link`);\n"
            + "  for (let i=0; i<links.length; i++) {\n"
            + "    links[i].style.setProperty('display', links[i].style.getPropertyValue('display') === 'none' ? 'block' : 'none');\n"
            + "  }\n"
            + "}\n"
            + "function showDetails(event) {\n"
            + "  console.log(event);\n"
            + "  document.getElementById('detailsDiv').innerHTML = document.getElementById(event.target.getAttribute('service')).innerHTML;\n"
            + "  document.getElementById('detailsDiv').style.height = '33vh';\n"
            + "  event.stopPropagation();\n"
            + "}\n"
            + "function hideDetails() {\n"
            + "  document.getElementById('detailsDiv').style.height = '0vh';\n"
            + "}\n"
            + "function shrinkDetails() {\n"
            + "  document.getElementById('detailsDiv').style.height = document.getElementById('detailsDiv').style.height === '66vh' ? '33vh' : '0vh';\n"
            + "}\n"
            + "function expandDetails() {\n"
            + "  document.getElementById('detailsDiv').style.height = '66vh';\n"
            + "}\n"
            # EC2 instances
            + "function showEc2InstanceTypes() {\n"
            + "  document.getElementById('instancesInBoth').innerHTML = returnNestedList({});\n".format(
                json.dumps(both_instances)
            )
            + "  document.getElementById('instancesInRegion1').innerHTML = returnNestedList({});\n".format(
                json.dumps(reg1_instances)
            )
            + "  document.getElementById('instancesInRegion2').innerHTML = returnNestedList({});\n".format(
                json.dumps(reg2_instances)
            )
            + "  showApiPresence();\n"
            + "  showRdsEngineVersions();\n"
            + "  setTimeout(attachListeners,1000);\n"
            + "}\n"
            # API presence
            + "function showApiPresence() {\n"
            + "  document.getElementById('apisInBoth').innerHTML = returnNestedList({});\n".format(
                json.dumps(both_apis)
            )
            + "  document.getElementById('apisInRegion1').innerHTML = returnNestedList({});\n".format(
                json.dumps(reg1_apis)
            )
            + "  document.getElementById('apisInRegion2').innerHTML = returnNestedList({});\n".format(
                json.dumps(reg2_apis)
            )
            + "}\n"
            # RDS engine versions
            + "function showRdsEngineVersions() {\n"
            + "  document.getElementById('dbEnginesInBoth').innerHTML = returnNestedList({});\n".format(
                json.dumps(both_dbengines)
            )
            + "  document.getElementById('dbEnginesInRegion1').innerHTML = returnNestedList({});\n".format(
                json.dumps(reg1_dbengines)
            )
            + "  document.getElementById('dbEnginesInRegion2').innerHTML = returnNestedList({});\n".format(
                json.dumps(reg2_dbengines)
            )
            + "}\n"
            + "\n"
            + "function returnNestedList(data) {\n"
            + "  let currentInstanceClass = null;"
            + "  let output = '';"
            + "  for (let i=0; i<data.length; i++) {\n"
            + "    let splitData = data[i].split('.');"
            + "    if (splitData.length > 1) {\n"
            + "        let thisInstanceClass = splitData[0];\n"
            + "        if (data[i].match(/mysql_aurora/)) {\n"
            + "          thisInstanceClass = data[i].split('mysql_aurora.')[0] + 'mysql_aurora';\n"
            + "        }\n"
            + "        if (currentInstanceClass === null) {\n"
            + "          output += `<ul class='nestedList'><li><span class='caret'>${thisInstanceClass}</span><ul class='nested'><li>${data[i]}</li>`;\n"
            + "          currentInstanceClass = thisInstanceClass;\n"
            + "        }\n"
            + "        else if (currentInstanceClass !== thisInstanceClass) {\n"
            + "          output += `</ul></li></ul><ul class='nestedList'><li><span class='caret'>${thisInstanceClass}</span><ul class='nested'><li>${data[i]}</li>`;\n"
            + "          currentInstanceClass = thisInstanceClass;\n"
            + "        }\n"
            + "        else {\n"
            + "          output += `<li>${data[i]}</li>`;\n"
            + "        }\n"
            + "    }\n"
            + "    else {\n"
            + "        output += `${data[i]}<br>`;\n"
            + "    }\n"
            + "  }\n"
            + "  return output;\n"
            + "}\n"
            + "function attachListeners() {\n"
            + "  let toggler = document.getElementsByClassName('caret');\n"
            + "  for (let i = 0; i < toggler.length; i++) {\n"
            + "    toggler[i].addEventListener('click', function() {\n"
            + "      this.parentElement.querySelector('.nested').classList.toggle('active');\n"
            + "      this.classList.toggle('caret-down');\n"
            + "    });\n"
            + "  }\n"
            + "}\n"
            + "</script>\n"
            + "<button onclick='changeRegions()'>Go</button>\n"
        )
        default_url_template = "https://cfn-resource-specifications-{}-prod.s3.{}.amazonaws.com/latest/CloudFormationResourceSpecification.json"
        china_url_template = "https://cfn-resource-specifications-{}-prod.s3.{}.amazonaws.com.cn/latest/gzip/CloudFormationResourceSpecification.json"
        cfn_service_docs_url_template = (
            "https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/{}.html"
        )
        cfn_resource_docs_url_template = (
            "https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/{}.html"
        )

        this_url = "https://region-comparison-tool.com/?region1={}&region2={}".format(
            region1, region2
        )

        try:
            r1_url_template = default_url_template
            r2_url_template = default_url_template
            if re.match(r"^cn", region1):
                r1_url_template = china_url_template
            if re.match(r"^cn", region2):
                r2_url_template = china_url_template
            reg1_url = r1_url_template.format(region1, region1)
            reg2_url = r2_url_template.format(region2, region2)
            # print(reg1_url)
            # print(reg2_url)
            reg1 = requests.get(reg1_url, timeout=9)
            print(reg1.raise_for_status())
            reg2 = requests.get(reg2_url, timeout=9)
            print(reg2.raise_for_status())
            if reg1.status_code == 200 and reg2.status_code == 200:
                reg1_resources = reg1.json()["ResourceTypes"]
                reg2_resources = reg2.json()["ResourceTypes"]
                reg1_props = reg1.json()["PropertyTypes"]
                reg2_props = reg2.json()["PropertyTypes"]

                all_services = {}
                reg2_services = {}
                reg1_services = {}
                csv_response = ""
                response = (
                    "<!DOCTYPE html><html lang='en' style='font-family: \"Amazon Ember\", sans-serif; background-color: #FF9900' xmlns:fb='http://ogp.me/ns/fb#'>"
                    + "<head><meta charset='utf-8'><title>Region Comparison Tool</title><meta name='viewport' content='width=device-width, initial-scale=1'><meta property='og:image' content='{}' />".format(
                        preview_image
                    )
                    + '<style>.greyBox{ background-color: #fcfcfc; border: 1px solid grey; border-radius: 10px; padding: 0px 17px; margin: 10px -15px; }.diffHeading{ position: fixed;left: 0px; right: 0px;margin: 0px; padding: 5px 20px; font-size: 18px; background: #eee; border-bottom: 1px solid lightgrey; }#detailsDiv{ transition: all 1s; position: fixed; bottom: 0vh; height: 0vh; overflow-y: scroll; left: 0; right: 0; background: white; border: 1px solid grey; box-shadow: 0px -8px 20px 0px rgba(0, 0, 0, 0.2);}.apiNotFound{border-radius: 3px;border: 1px solid #FF9900; padding: 2px 5px; color: #FF9900; margin-bottom: -2px; font-size: small;}.apiExists{border-radius: 3px;background-color: #FF9900; padding: 2px 5px; color: white; margin-bottom: -2px; font-size: small;}.ec2Boxes{height:310px;overflow-y:auto;border:1px solid grey;padding:10px;border-radius:10px;margin: 2% 0%;}.nestedList,ul{list-style-type:none}.nestedList{margin:0;padding:0}.caret{cursor:pointer;user-select:none}.caret::before{content:"\\25B6";color:#000;display:inline-block;margin-right:6px}.caret-down::before{transform:rotate(90deg)}.nested{display:none}.active{display:block}.redLink { clear:both; text-decoration: none; display: block };.orangeLink { clear:both; text-decoration: none; display: block };.greenLink { clear:both; text-decoration: none; display: block };.purpleLink { clear:both; text-decoration: none; display: block };.alert { background-color: #fff8cf; border: 1px solid red; border-radius: 10px; padding: 10px; margin: 10px 0px; }\nbutton { cursor: pointer; background-color: #ffeccf; color: black; border: 1px solid black; border-radius: 5px; font-size: inherit; }\nselect { cursor: pointer;background-color: #ffeccf; color: black; border: 1px solid black; border-radius: 3px; font-size: inherit; }\nh1 { margin: 2% 0px 0px 0px }\nh2,h3,h4,h5,h6 { margin:2% 0% 0%; }\nh6 {font-size: 1em; font-weight: unset; margin: 1px;}\nh5 {font-size: 1.1em; margin-top: 4px}\nh4 { font-size: 1.2em;font-style: italic;}\nh3 {font-size: 1.2em;  white-space: nowrap;}\n.nowrap {white-space: nowrap; display: inline-block; }\n.legend {display: block; margin-bottom: 5px; }\na {cursor: pointer; white-space: nowrap; margin-bottom: 6px; display: inline-block; text-decoration: underline; text-decoration-thickness: 1px; text-decoration-style: solid; color: #000000; text-underline-offset: 3px; } a[target="_blank"]::after { content: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAQElEQVR42qXKwQkAIAxDUUdxtO6/RBQkQZvSi8I/pL4BoGw/XPkh4XigPmsUgh0626AjRsgxHTkUThsG2T/sIlzdTsp52kSS1wAAAABJRU5ErkJggg==); margin: 0 3px 0 5px;}\nbody {margin: 2% 5%; border: 1px grey solid; border-radius: 10px; padding: 10px 4%; background-color: white;}\n.datadivs { float:left; width: 100%; }\n.uplabel { display:none; width: 0px; }\n@media screen and (min-width: 850px) { .datadivs {  width: 33%; }}</style></head>'
                    + "<body onload='showEc2InstanceTypes()'><div onclick='hideDetails()'><h1>Region Comparison Tool</h1><h2>"
                    + get_nice_name(region1)
                    + " → "
                    + get_nice_name(region2)
                    + "</h2>"
                )
                response += "\n<div style='max-width: 900px'>"
                response += "<p>This tool fetches the CloudFormation resource spec from each Region and compares them, allowing you to see differences in service parity. It also compares the APIs, EC2 Instance Types and RDS/Aurora database engines that are available in the two selected Regions.</p>"
                response += "<p>This comparison can be especially useful when assessing Regions you (or a customer) might be looking to expand into. It can also alert you to missing features when a service has been newly released in a Region and may not have feature parity on day one.</p>"
                response += "<div class='alert'><b>NOTE:</b> This tool only reports on what is defined in publicly-available data. Some service features and configurations will require additional investigation to establish whether or not they are supported in a given Region.</div>"
                response += "\n<div class='greyBox'>"
                response += "<p><b>To use:</b> choose any two regions and click the <b>Go</b> button: </p>"
                response += (
                    "<p>Compare source region <span class='nowrap'>"
                    + region_dropdown_1
                    + "</span> with destination region <span class='nowrap'>"
                    + region_dropdown_2
                    + "</span> "
                    + go_button
                    + spinner_image.replace("alt='spinner'", "id='spinner'")
                )
                response += "<p>The tool expects the more featured region to be on the left, so results are formatted with a slight bias towards that scenario.</p>"
                response += "</div>"
                response += "<p style='font-size: smaller'><i>These results were generated on {} and reflect the data available at {} (UTC).</i><br/>If you believe these results are out of date, you can force a refresh by clicking this <button onclick='changeRegions(true)'>Refresh</button> button.</p>".format(
                    today.strftime("%a %d %b %Y"),
                    today.strftime("%I:%M%p"),
                )
                response += "<p>{} You can <button onclick='changeRegions(true,true)'>Download</button> this data as CSV.</p>".format(
                    download_image
                )
                response += (
                    '<p>The CloudFormation source data is <a target="_blank" href="'
                    + reg1_url
                    + '">here for '
                    + region1
                    + '</a> and <a target="_blank" href="'
                    + reg2_url
                    + '">here for '
                    + region2
                    + "</a></p>"
                )
                response += "<p><b>Note:</b> there can be a delay of a week or more between a service being released in a new Region and CloudFormation support becoming available and thus making the service visible here. APIs appear first so you may find a service has a service API present in a Region before CloudFormation supports it.</p>"
                # response += "<h3>Technical Details</h3>"
                # response += "<p>The data displayed in this tool is sourced from the <a target='_blank' href='https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-resource-specification.html'>CloudFormation resource specification</a> and the <a target='_blank' href='https://aws.amazon.com/blogs/aws/subscribe-to-aws-daily-feature-updates-via-amazon-sns/'>AWS Daily Feature Updates</a> service.</p>"
                # response += "<p>This serverless tool is built using <a href='https://aws.amazon.com/serverless/sam/' target='_blank'>AWS SAM</a> and uses <a href='https://aws.amazon.com/api-gateway/' target='_blank'>AWS API Gateway</a> to handle inbound requests. API Gateway invokes python code running in <a href='https://aws.amazon.com/lambda/' target='_blank'>AWS Lambda</a> to build and output the response. <a href='https://aws.amazon.com/dynamodb/' target='_blank'>AWS DynamoDB</a> is used to log &amp; cache calculated comparisons.</p>"
                # response += "<p>By default, any comparison of two Regions is cached for 24 hours, but it can be force-refreshed if needed. It's almost certainly not needed unless you can see the generated date above is older than 24 hours.</p>"
                # response += "<p>If you have any feedback or feature suggestions for this tool you can email the author Guy Morton (<i>guymor</i> at <i>amazon&#8228;com</i>).</p>"
                response += "</div>"

                for resource_type in reg1_resources:
                    if "AMZN" in resource_type:
                        continue
                    resource_type_parts = resource_type.split("::")
                    if len(resource_type_parts) > 2:
                        service_name = (
                            resource_type_parts[0] + "::" + resource_type_parts[1]
                        )
                        resource_name = resource_type_parts[2]
                        if service_name not in reg1_services:
                            all_services[service_name] = {}
                            reg1_services[service_name] = {}
                        if resource_type in reg2_resources:
                            reg1_services[service_name][resource_name] = "reg1,reg2"
                        if resource_type not in reg2_resources:
                            reg1_services[service_name][resource_name] = "reg1"
                for resource_type in reg1_props:
                    if "AMZN" in resource_type:
                        continue
                    resource_type_parts = resource_type.split("::")
                    if len(resource_type_parts) > 2:
                        service_name = (
                            resource_type_parts[0] + "::" + resource_type_parts[1]
                        )
                        resource_name = resource_type_parts[2]
                        if service_name not in reg1_services:
                            all_services[service_name] = {}
                            reg1_services[service_name] = {}
                        if resource_type in reg2_props:
                            reg1_services[service_name][resource_name] = "reg1,reg2"
                        if resource_type not in reg2_props:
                            reg1_services[service_name][resource_name] = "reg1"

                for resource_type in reg2_resources:
                    if "AMZN" in resource_type:
                        continue
                    resource_type_parts = resource_type.split("::")

                    if len(resource_type_parts) > 2:
                        service_name = (
                            resource_type_parts[0] + "::" + resource_type_parts[1]
                        )
                        resource_name = resource_type_parts[2]
                        if service_name not in reg2_services:
                            all_services[service_name] = {}
                            reg2_services[service_name] = {}
                        if resource_type in reg1_resources:
                            reg2_services[service_name][resource_name] = "reg1,reg2"
                        if resource_type not in reg1_resources:
                            reg2_services[service_name][resource_name] = "reg2"
                for resource_type in reg2_props:
                    if "AMZN" in resource_type:
                        continue
                    resource_type_parts = resource_type.split("::")

                    if len(resource_type_parts) > 2:
                        service_name = (
                            resource_type_parts[0] + "::" + resource_type_parts[1]
                        )
                        resource_name = resource_type_parts[2]
                        if service_name not in reg2_services:
                            all_services[service_name] = {}
                            reg2_services[service_name] = {}
                        if resource_type in reg1_props:
                            reg2_services[service_name][resource_name] = "reg1,reg2"
                        if resource_type not in reg1_props:
                            reg2_services[service_name][resource_name] = "reg2"

                in_both = {}
                reg1_only = {}
                reg2_only = {}
                csv_array = [
                    [
                        "Service",
                        "Resource",
                        "Type",
                        "Status",
                        "In Both",
                        region1,
                        region2,
                        "Documentation",
                        "Details",
                    ]
                ]
                for service in all_services:
                    in_both[service] = {}
                    reg1_only[service] = {}
                    reg2_only[service] = {}

                    if service in reg2_services:
                        for resource in reg2_services[service]:
                            if reg2_services[service][resource] == "reg1,reg2":
                                in_both[service][resource] = True
                            elif reg2_services[service][resource] == "reg2":
                                reg2_only[service][resource] = True
                    if service in reg1_services:
                        for resource in reg1_services[service]:
                            if reg1_services[service][resource] == "reg1,reg2":
                                in_both[service][resource] = True
                            elif reg1_services[service][resource] == "reg1":
                                reg1_only[service][resource] = True

                links_array = []
                service_states = {}
                colours = {
                    "red": "#d00",
                    "green": "#0c0",
                    "purple": "#90f",
                    "orange": "#f90",
                }
                red_dot = (
                    "<span style='font-size: .7em; color:{}'>&#11044;</span>".format(
                        colours["red"]
                    )
                )
                orange_dot = (
                    "<span style='font-size: .7em; color:{}'>&#11044;</span>".format(
                        colours["orange"]
                    )
                )
                green_dot = (
                    "<span style='font-size: .7em; color:{}'>&#11044;</span>".format(
                        colours["green"]
                    )
                )
                purple_dot = (
                    "<span style='font-size: .7em; color:{}'>&#11044;</span>".format(
                        colours["purple"]
                    )
                )
                service_dots = {}
                service_colours = {}
                colour = "red"
                for service in all_services:
                    dot = red_dot
                    colour = "red"
                    service_states[service] = "Not Available"
                    service_colours[service] = colours["red"]
                    if (
                        len(in_both[service]) > 0
                        and len(reg1_only[service]) == 0
                        and len(reg2_only[service]) == 0
                    ):
                        dot = green_dot
                        colour = "green"
                        service_states[service] = "Parity"
                        service_colours[service] = colours["green"]
                    elif (
                        len(in_both[service]) == 0
                        and len(reg1_only[service]) > 0
                        and len(reg2_only[service]) == 0
                    ):
                        dot = red_dot
                        colour = "red"
                        service_states[service] = "Unavailable"
                        service_colours[service] = colours["red"]
                    elif (
                        len(in_both[service]) >= 0
                        and len(reg1_only[service]) > 0
                        and len(reg2_only[service]) == 0
                    ):
                        dot = orange_dot
                        colour = "orange"
                        service_states[service] = "Missing Features"
                        service_colours[service] = colours["orange"]
                    elif len(in_both[service]) >= 0 and len(reg2_only[service]) > 0:
                        dot = purple_dot
                        colour = "purple"
                        service_states[service] = "Extra Features"
                        service_colours[service] = colours["purple"]
                    service_dots[service] = dot
                    api_info = ""
                    api_name = service.replace("AWS::", "").lower()
                    if colour == "red" and (
                        check_service_in_api_list(api_name, both_apis) or check_service_in_api_list(api_name, reg2_apis)
                    ):
                        api_info = "<span class='apiExists' id='{}'>API</span>".format(
                            api_name
                        )
                    elif colour == "purple" and (
                        check_service_in_api_list(api_name, both_apis) or check_service_in_api_list(api_name, reg1_apis)
                    ):
                        api_info = "<span class='apiExists' id='{}'>API</span>".format(
                            api_name
                        )
                    elif colour != "green" and not (
                        check_service_in_api_list(api_name, both_apis) or check_service_in_api_list(api_name, reg1_apis) or check_service_in_api_list(api_name, reg2_apis)
                    ):
                        api_info = "<span class='apiNotFound' id='{}'>?</span>".format(
                            api_name
                        )
                    links_array.append(
                        "<div class='{}Link' style='margin-right: 7px;'><a service='{}' onclick='showDetails(event)'>{}</a> {} {}</div>".format(
                            colour,
                            service.replace("::", ""),
                            service.replace("AWS::", ""),
                            dot,
                            api_info,
                        )
                    )
                link_div = "\n<div style='float:left; padding-right: 20px; padding-top: 10px; padding-bottom: 10px; width: 230px'>"
                # <a id='top'></a>
                response += (
                    "\n<div><h2>Service Summary: {} → {}</h2>".format(
                        get_nice_name(region1), get_nice_name(region2)
                    )
                )
                response += "\n<div class='greyBox' style='margin-bottom: 15px;'>"
                response += "\n<p><b>What the icons mean</b> <i>(Note you can click the dotted legends to hide those items.)</i></p>"
                response += "<div style='display: grid; grid-template-columns: 1fr 1fr; column-gap: 20px;'>"
                response += "<div class='legend' style='cursor: pointer; text-decoration: none;' id='greenLegend' onclick=toggleVisibity('green')>{} available in Both Regions</div>".format(
                    green_dot
                )
                response += "<div class='legend' style='cursor: pointer; text-decoration: none;' id='redLegend' onclick=toggleVisibity('red')>{} only available in Source Region</div>".format(
                    red_dot
                )
                response += "<div class='legend' style='cursor: pointer; text-decoration: none;' id='orangeLegend' onclick=toggleVisibity('orange')>{} some resources only in Source Region</div>".format(
                    orange_dot
                )
                response += "<div class='legend' style='cursor: pointer;text-decoration: none;' id='purpleLegend' onclick=toggleVisibity('purple')>{} some resources only in Destination Region</div>".format(
                    purple_dot
                )
                response += "</div>"
                response += "<p>Where either the Source or Destination Region shows a service as missing, we will show these icons to indicate the API status in that Region. <b>If neither of these icon is shown it means no API was found.</b></p>"
                response += "<div style='display: grid; grid-template-columns: 1fr 1fr; column-gap: 20px;'>"
                response += "<div class='legend' style='margin-top: 5px'><span class='apiExists'>API</span> API is present, so some level of support for the service is available</div>"
                response += "<div class='legend' style='margin-top: 5px'><span class='apiNotFound'>?</span> Unable to identify which API relates to this service</div>"
                response += "</div>"
                response += "<p><i>If the data in this tool is ambiguous, you should check the console to see which services (and service features) are supported.</i></p>"
                response += "</div>{}".format(link_div)
                numlinks_in_div = 15
                index = 0
                for link in links_array:
                    if index > 0 and index % numlinks_in_div == 0:
                        response += "</div>{}".format(link_div)
                    response += "{}".format(link)
                    index = index + 1

                response += "</div></div>"
                response += "<div style='width: 100%; clear: both'></div>"
                response += "<hr>"
                # API presence comparison
                response += "<div id='apiPresenceDisplay'><h2>API Presence</h2></div>"
                response += "<div style='display: grid; grid-template-columns: 1fr 1fr 1fr; column-gap: 10px;margin-bottom: 10px;'>"
                response += "<div><h4>In Both Regions</h4></div>"
                response += "<div><h4>Only in {}</h4></div>".format(
                    get_nice_name(region1)
                )
                response += "<div><h4>Only in {}</h4></div>".format(
                    get_nice_name(region2)
                )
                response += "<div class='ec2Boxes' id='apisInBoth'>{}</div>".format(
                    spinner_image
                )
                response += "<div class='ec2Boxes' id='apisInRegion1'>{}</div>".format(
                    spinner_image
                )
                response += "<div class='ec2Boxes' id='apisInRegion2'>{}</div>".format(
                    spinner_image
                )
                response += "</div>"
                # EC2 instance availability
                response += "<div id='ec2InstanceTypeDisplay'><h2>EC2 Instance Type Availability</h2></div>"
                response += "<div style='display: grid; grid-template-columns: 1fr 1fr 1fr; column-gap: 10px;margin-bottom: 10px;'>"
                response += "<div><h4>In Both Regions</h4></div>"
                response += "<div><h4>Only in {}</h4></div>".format(
                    get_nice_name(region1)
                )
                response += "<div><h4>Only in {}</h4></div>".format(
                    get_nice_name(region2)
                )
                response += (
                    "<div class='ec2Boxes' id='instancesInBoth'>{}</div>".format(
                        spinner_image
                    )
                )
                response += (
                    "<div class='ec2Boxes' id='instancesInRegion1'>{}</div>".format(
                        spinner_image
                    )
                )
                response += (
                    "<div class='ec2Boxes' id='instancesInRegion2'>{}</div>".format(
                        spinner_image
                    )
                )
                response += "</div>"
                # DB Engine availability
                response += "<div id='dbEngineTypeDisplay'><h2>RDS Engine Version Availability</h2></div>"
                response += "<div style='display: grid; grid-template-columns: 1fr 1fr 1fr; column-gap: 10px;margin-bottom: 10px;'>"
                response += "<div><h4>In Both Regions</h4></div>"
                response += "<div><h4>Only in {}</h4></div>".format(
                    get_nice_name(region1)
                )
                response += "<div><h4>Only in {}</h4></div>".format(
                    get_nice_name(region2)
                )
                response += (
                    "<div class='ec2Boxes' id='dbEnginesInBoth'>{}</div>".format(
                        spinner_image
                    )
                )
                response += (
                    "<div class='ec2Boxes' id='dbEnginesInRegion1'>{}</div>".format(
                        spinner_image
                    )
                )
                response += (
                    "<div class='ec2Boxes' id='dbEnginesInRegion2'>{}</div>".format(
                        spinner_image
                    )
                )
                response += "</div>"

                response += "<div>"
                response += "<h3>Technical Details</h3>"
                response += "<p>The data displayed in this tool is sourced from the <a target='_blank' href='https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-resource-specification.html'>CloudFormation resource specification</a> and the <a target='_blank' href='https://aws.amazon.com/blogs/aws/subscribe-to-aws-daily-feature-updates-via-amazon-sns/'>AWS Daily Feature Updates</a> service.</p>"
                response += "<p>This serverless tool is built using <a href='https://aws.amazon.com/serverless/sam/' target='_blank'>AWS SAM</a> and uses <a href='https://aws.amazon.com/api-gateway/' target='_blank'>AWS API Gateway</a> to handle inbound requests. API Gateway invokes python code running in <a href='https://aws.amazon.com/lambda/' target='_blank'>AWS Lambda</a> to build and output the response. <a href='https://aws.amazon.com/dynamodb/' target='_blank'>AWS DynamoDB</a> is used to log &amp; cache calculated comparisons.</p>"
                response += "<p>By default, any comparison of two Regions is cached for 24 hours, but it can be force-refreshed if needed. It's almost certainly not needed unless you can see the generated date above is older than 24 hours.</p>"
                response += "<p>If you have any feedback or feature suggestions for this tool you can email the author Guy Morton (<i>guymor</i> at <i>amazon&#8228;com</i>).</p>"
                response += "</div>"

                ##### 
                # Service Details cards
                #####
                for service in all_services:
                    link = cfn_service_docs_url_template.format(
                        service.replace("::", "_")
                    )
                    response += '\n<div id="{}" style="display: none;">\n'.format(service.replace("::", ""))
                    response += "<div class='diffHeading'>"
                    response += "\n<div style='float: right; display: grid; grid-template-columns: 1fr 1fr 1fr; column-gap: 20px;'><div onclick='expandDetails()'>{}</div> <div onclick='shrinkDetails()'>{}</div> <div onclick='hideDetails()'>{}</div></div>".format(up_image,down_image,close_image)
                    response += "<p style='margin: 3px 0px'>Service Details - CloudFormation Differences</p></div>"
                    response += '\n<div style="padding: 20px; margin-top: 30px;">\n'
                    response += "\n<h3 style=\"margin: 0px\"><span style='font-size: .7em; color:{}; vertical-align: text-top'>&#11044;</span> <a target='_blank' href=\"{}\">{}</a></h3>\n".format(
                        service_colours[service], link, service
                    )
                    csv_array.append(
                        [
                            service,
                            service,
                            "Service",
                            service_states[service],
                            "",
                            "",
                            "",
                            link,
                            this_url + "#{}".format(service.replace("::", "")),
                        ]
                    )
                    response += "\n<div class='datadivs'>"
                    if service in in_both:
                        response += '<h4 style="margin: 5px 0px">In Both</h4>'
                        for resource in sorted(in_both[service]):
                            if "." in resource:
                                csv_array.append(
                                    [
                                        service,
                                        resource,
                                        "Entity",
                                        service_states[service],
                                        "Yes",
                                        "Yes",
                                        "Yes",
                                    ]
                                )
                                response += "<h6>&#9656;&nbsp;" + resource + "</h6>"
                            else:
                                resource_link = cfn_resource_docs_url_template.format(
                                    service.replace("::", "-resource-").lower()
                                    + "-"
                                    + resource.lower()
                                )
                                csv_array.append(
                                    [
                                        service,
                                        resource,
                                        "Resource",
                                        service_states[service],
                                        "Yes",
                                        "Yes",
                                        "Yes",
                                        resource_link,
                                    ]
                                )
                                response += (
                                    "<h5><a target='_blank' href=\"{}\">{}</a></h5>".format(
                                        resource_link, resource
                                    )
                                )
                    response += "<p>&nbsp;</p></div>"
                    response += "\n<div class='datadivs'>"

                    if service in reg1_only:
                        response += (
                            '<h4 style="margin: 5px 0px">Only in '
                            + get_nice_name(region1)
                            + "</h4>"
                        )
                        for resource in sorted(reg1_only[service]):
                            if "." in resource:
                                csv_array.append(
                                    [
                                        service,
                                        resource,
                                        "Entity",
                                        service_states[service],
                                        "No",
                                        "Yes",
                                        "No",
                                    ]
                                )
                                response += "<h6>&#9656;&nbsp;" + resource + "</h6>"
                            else:
                                resource_link = cfn_resource_docs_url_template.format(
                                    service.replace("::", "-resource-").lower()
                                    + "-"
                                    + resource.lower()
                                )
                                csv_array.append(
                                    [
                                        service,
                                        resource,
                                        "Resource",
                                        service_states[service],
                                        "No",
                                        "Yes",
                                        "No",
                                        resource_link,
                                    ]
                                )
                                response += "<h5><a target='_blank' href=\"{}\">{}</a></h5>".format(
                                    resource_link, resource
                                )

                    response += "<p>&nbsp;</p></div>"
                    response += "\n<div class='datadivs'>"

                    if service in reg2_only:
                        response += (
                            '<h4 style="margin: 5px 0px">Only in '
                            + get_nice_name(region2)
                            + "</h4>"
                        )
                        for resource in sorted(reg2_only[service]):
                            if "." in resource:
                                csv_array.append(
                                    [
                                        service,
                                        resource,
                                        "Entity",
                                        service_states[service],
                                        "No",
                                        "No",
                                        "Yes",
                                    ]
                                )
                                response += "<h6>&#9656;&nbsp;" + resource + "</h6>"
                            else:
                                resource_link = cfn_resource_docs_url_template.format(
                                    service.replace("::", "-resource-").lower()
                                    + "-"
                                    + resource.lower()
                                )
                                csv_array.append(
                                    [
                                        service,
                                        resource,
                                        "Resource",
                                        service_states[service],
                                        "No",
                                        "No",
                                        "Yes",
                                        resource_link,
                                    ]
                                )
                                response += "<h5><a target='_blank' href=\"{}\">{}</a></h5>".format(
                                    resource_link, resource
                                )

                        response += "<p>&nbsp;</p></div>"
                    response += "</div></div>"
                response += "</div></div><div id='detailsDiv' class='detailsDiv'></div></body></html>"

                csv_response = ""
                for line in csv_array:
                    csv_response += ",".join(line)
                    csv_response += "\n"

                cache_response = {
                    "id": today_resultname,
                    "response": zlib.compress(response.encode()),
                }
                caching_table.put_item(TableName=cache_table, Item=cache_response)
            else:
                response = "Error - perhaps bad inputs for region1 or region2?"

        except requests.RequestException as e:
            # Send some context about this error to Lambda Logs
            print(e)
            response = "Error - perhaps bad inputs for region1 or region2?"
    if format == "html":
        return {
            "statusCode": 200,
            "headers": {"content-type": "text/html"},
            "body": response,
        }
    elif format == "csv":
        return {
            "statusCode": 200,
            "headers": {
                "content-type": "text/csv",
                "content-disposition": "attachment; filename={}.csv".format(
                    today_resultname
                ),
            },
            "body": csv_response,
        }


def get_instance_types(region1, region2):
    instance_types_url = "https://aws-new-features.s3.us-east-1.amazonaws.com/html/ec2_instance_types.json"
    instance_types_get = requests.get(instance_types_url, timeout=9)
    reg1 = []
    reg2 = []
    both = []
    if instance_types_get.status_code == 200 and instance_types_get.status_code == 200:
        instance_types = instance_types_get.json()
        (reg1, reg2, both) = get_from_data(region1, region2, instance_types)
    return (reg1, reg2, both)


def get_db_engines(region1, region2):
    instance_types_url = "https://aws-new-features.s3.us-east-1.amazonaws.com/html/rds_engine_versions.json"
    instance_types_get = requests.get(instance_types_url, timeout=9)
    reg1 = []
    reg2 = []
    both = []
    if instance_types_get.status_code == 200 and instance_types_get.status_code == 200:
        instance_types = instance_types_get.json()
        (reg1, reg2, both) = get_from_data(region1, region2, instance_types)
    return (reg1, reg2, both)


def get_api_presence(region1, region2):
    api_presence_url = (
        "https://aws-new-features.s3.us-east-1.amazonaws.com/html/aws_services.json"
    )
    api_presence_get = requests.get(api_presence_url, timeout=9)
    reg1 = []
    reg2 = []
    both = []
    if api_presence_get.status_code == 200 and api_presence_get.status_code == 200:
        instance_types = api_presence_get.json()
        (reg1, reg2, both) = get_from_data(region1, region2, instance_types)
    return (reg1, reg2, both)


def get_from_data(region1, region2, data):
    reg1 = []
    reg2 = []
    both = []
    for key in data:
        if (
            region1 in data[key]
            and data[key][region1] == key
            and region2 in data[key]
            and data[key][region2] == key
        ):
            both.append(key)
        else:
            if region1 in data[key] and data[key][region1] == key:
                reg1.append(key)
            if region2 in data[key] and data[key][region2] == key:
                reg2.append(key)
    return (reg1, reg2, both)


region_map = {
    "us-east-1": "US: N. Virginia",
    "us-east-2": "US: Ohio",
    "us-west-1": "US: N. California",
    "us-west-2": "US: Oregon",
    "ap-southeast-4": "AU: Melbourne",
    "ap-south-1": "IN: Mumbai",
    "ap-northeast-3": "JP: Osaka",
    "ap-northeast-2": "KR: Seoul",
    "ap-southeast-1": "SG: Singapore",
    "ap-southeast-2": "AU: Sydney",
    "ap-southeast-5": "MY: Malaysia",
    "ap-northeast-1": "JP: Tokyo",
    "ca-central-1": "CA: Central Canada",
    "eu-central-1": "DE: Frankfurt",
    "eu-west-1": "IE: Ireland",
    "eu-west-2": "GB: London",
    "eu-west-3": "FR: Paris",
    "eu-north-1": "SE: Stockholm",
    "sa-east-1": "BR: São Paulo",
    "af-south-1": "SA: Cape Town",
    "ap-east-1": "CN: Hong Kong",
    "ap-south-2": "IN: Hyderabad",
    "ap-southeast-3": "ID: Jakarta",
    "ca-west-1": "CA: Calgary",
    "eu-central-2": "CH: Zurich",
    "eu-south-1": "IT: Milan",
    "eu-south-2": "ES: Spain",
    "il-central-1": "IL: Tel Aviv",
    "me-central-1": "AE: UAE",
    "me-south-1": "BH: Bahrain",
    "us-gov-east-1": "US: GovCloud East",
    "us-gov-west-1": "US: GovCloud West",
    "cn-north-1": "CN: Beijing",
    "cn-northwest-1": "CN: Ningxia",
}


def get_nice_name(region, include_country=False):
    if region in region_map:
        if include_country:
            return region_map[region]
        else:
            return region_map[region].split(": ")[1]
    else:
        return region

def check_service_in_api_list(service, api_array):
    if get_api_from_service(service) in api_array:
        return True
    return False

def get_api_from_service(service):
    match service:
        case "acmpca":
            return "acm-pca"
        case "amazonmq":
            return "mq"
        case "applicationinsights":
            return "application-insights"
        case "backupgateway":
            return "backup-gateway"
        case "workspacesweb":
            return "workspaces-web"
        case "servicecatalogappregistry":
            return "servicecatalog-appregistry"
        case "wafregional":
            return "waf-regional"
        case "wafv2":
            return "waf"
        case "vpclattice":
            return "vpc-lattice"
        case "supportapp":
            return "support-app"
        case "sso":
            return "sso-oidc"
        case "ssmcontacts":
            return "ssm-contacts"
        case "ssmincidents":
            return "ssm-incidents"
        case "ssmquicksetup":
            return "ssm-quicksetup"
        case "resourceexplorer2":
            return "resource-explorer-2"
        case "ce":
            return "costexplorer"
        case "emrcontainers":
            return "emr-containers"
        case "emrserverless":
            return "emr-serverless"
        case "neptunegraph":
            return "neptune-graph"
        case "networkfirewall":
            return "network-firewall"
        case "lex":
            return "lex-runtime"
        case "elasticloadbalancing":
            return "elb"
        case "certificatemanager":
            return "acm"
        case "cognito":
            return "cognito-idp"
        case "inspectorv2":
            return "inspector2"
        case "redshiftserverless":
            return "redshift-serverless"
        case "pcaconnectorad":
            return "pca-connector-ad"
        case "pcaconnectorscep":
            return "pca-connector-scep"
        case "route53recoverycontrolconfig":
            return "route53-recovery-control-config"
        case "route53applicationrecoverycontrol":
            return "route53-application-recovery-controller"
        case "paymentcryptography":
            return "payment-cryptography"
        case "licensemanager":
            return "license-manager"
        case "customerprofiles":
            return "customer-profiles"
        case "codestarnotifications":
            return "codestar-notifications"
        case "codestarconnections":
            return "codestar-connections"
        case "codeconnections":
            return "codestar-connections"
        case "arczonalshift":
            return "arc-zonal-shift"
        case "pinpointemail":
            return "pinpoint-email"
        case "voiceid":
            return "voice-id"
        case "kendraranking":
            return "kendra-ranking"
        case "deadlinecloud":
            return "deadline-cloud"
        case "devopsguru":
            return "devops-guru"
        case "codegurureviewer":
            return "codeguru-reviewer"
        case "location":
            return "amazonlocationservice"
        case "nimblestudio":
            return "nimble"
        case _:
            return service
         
        

