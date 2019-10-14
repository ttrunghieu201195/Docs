import requests
import json

from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
import getpass
import re
from jira import JIRA
import xlsxwriter 
import pip

# packages = ['requests', 'json', 'BeautifulSoup', 'HTTPBasicAuth', 'getpass', 're', 'JIRA', 'xlsxwriter']

# for package in packages:
	# try:
		# import package
	# except ImportError:
		# pip.main(['install', '--user', package])

members = '(chinh.nguyen.ym, hieu.tran.eb, nam.nguyen.te, nguyen.duong.uw, phuong.nguyen.px, van.tran.yg, vien.nguyen.uj, tung.tran.banvien, tien.truong-hoang.banvien, vinh.luong.xz, hoang.nguyen.te)'

bv_members = '(huy.tran-quockhang.banvien, son.nguyen.banvien)'

sprint_reg = re.compile('.*id=(?P<id>[0-9]+).*name=(?P<name>[^,]+).*startDate=(?P<startDate>[^T]+).*endDate=(?P<endDate>[^T]+).*', flags=re.S)

# ID of page initial documents list v7.7
pageid = '62981409'

# Get content of page with page ID
def get_content_page(pageid):
	# url of page
	url_page = 'https://jira.renesas.eu/confluence/rest/api/content/' + pageid
	# send request
	r = requests.get(url_page, auth = (user, pw))
	# get version of page
	pageVer = str(r.json()['version']['number'])
	print(pageVer)
	
	# url to get content of page
	url = 'https://jira.renesas.eu/confluence/rest/experimental/content/' + pageid + '/version/' + pageVer + '?expand=content.body.storage'
	# send request
	r = requests.get(url, auth = (user, pw))

	# Get content of page
	html_content = r.json()['content']['body']['storage']['value']
	# return content with html format
	return BeautifulSoup(html_content, "html.parser")

#Parse data from "initial documents list" page
def parse_data():
	# get content of page
	content = get_content_page(pageid)
	# initial list to contain data
	rows = []
	# parse content and store data to list
	for tr in content.findAll("tr"):
		cells = []
		for td in tr.findAll("td"):
			cells.append(td.text)
		rows.append(cells)
	# delete empty row first
	del rows[0]
	
	dict = {}
	returned_dict = {}
	# process string
	for row in rows:
		if 'IDE-' in row[0]:
			row[0] = row[0][row[0].find('IDE-'):len(row[0])]
		dict = {'Requirements': row[1], 'Design': row[2], 'Unit Test': row[3], 'JUnit': row[4], 'Functional Test': row[5], 'Help Update': row[6], 'Status': row[7], 'Note': row[8]}
		returned_dict[row[0]] = dict
	return returned_dict

# Get list issues
def get_list_issues(issues):
	list = []
	for issue in issues:
		list.append(str(issue))
	return list

# Get assignee of issue
def get_assignee_of_issue(issueId):
	issue = acc.issue(issueId)
	return issue.fields.assignee

# Check if there are IT, UT
def get_issue_links(issueId, issueInfo):
	issue = acc.issue(issueId)
	for link in issue.fields.issuelinks:
		if hasattr(link, "outwardIssue"):
			# print(link.outwardIssue.fields.summary)
			typeOfTest = link.outwardIssue.fields.summary
			if '[IT]' in typeOfTest:
				issueInfo['Functional Test'] = 'YES'
			elif '[UT]' in typeOfTest:
				issueInfo['Unit Test'] = 'YES'
			elif '[DevTest]' in typeOfTest:
				issueInfo['Unit Test'] = 'YES'
				issueInfo['Functional Test'] = 'YES'

# Check if there are FS, DS, Manual
def get_remote_links(issueId, issueInfo):
	dict = {}
	ReqNote = acc.issue(issueId).fields.customfield_11702
	print(str(issueId) + "-" + str(ReqNote))
	doc_req = []
	if ReqNote != None:
		for element in acc.issue(issueId).fields.customfield_11702:
			doc_req.append(element.value)
	
	for link_id in acc.remote_links(issueId):
		remote_link = acc.remote_link(issueId, link_id)
		if hasattr(remote_link.application, 'type') and 'confluence' in remote_link.application.type:
			link = remote_link.object.url
			pageId = link[link.find('pageId=')+7 : len(link)]
			url = 'https://jira.renesas.eu/confluence/rest/api/content/' + pageId
			r = requests.get(url, auth = (user, pw))
			title = r.json()['title']
			if 'Functional Specification' in title:
				issueInfo['Requirements'] = 'YES,NO'
				if ReqNote != None and 'Requirements' in doc_req:
					issueInfo['Requirements'] = 'YES,YES'
			elif 'Detailed Specification' in title or issueId in title:
				issueInfo['Design'] = 'YES,NO'
				if ReqNote != None and 'Design' in  doc_req:
					issueInfo['Design'] = 'YES,YES'
			elif 'Manual' in title:
				issueInfo['Help Update'] = 'YES,NO'
				if ReqNote != None and 'Help' in doc_req:
					issueInfo['Help Update'] = 'YES,YES'

# Is there JUnit for issue
def isJUnit(issueId):
	for comment in acc.comments(issueId):
		if 'Commit Message' in comment.body and 'JUnit' in comment.body:
			return 'YES'
	return 'NO'

# get info of issues (FS, DS, UT, JUnit, IT, Manual, ...)
# Return list of issue (each issue is dict which contains status of issue)
def get_issue_info():
	retro_filter = 'Type not in (Test, Sub-task, Epic, "Product Specification", Task) AND (assignee in ' + members + ' OR (assignee in ' + bv_members + '))' + ' AND sprint = ' + sprint_id + ' AND status in (Resolved, Verification)'
	print(retro_filter)
	issues = acc.search_issues(retro_filter)
	list_issues = []
	for issue in get_list_issues(issues):
		# initial issue information
		issueInfo = {'Feature': issue, 'Requirements': 'NO,NO', 'Design': 'NO,NO', 'Unit Test': 'NO', 'JUnit': 'NO', 'Functional Test': 'NO', 'Help Update': 'NO,NO', 'Status': '', 'Note': ''}
		# Update info
		get_issue_links(issue, issueInfo)
		get_remote_links(issue, issueInfo)
		issueInfo['JUnit'] = isJUnit(issue)
		list_issues.append(issueInfo)
	return list_issues

# Sprint planning checking
def sprint_planning_checking():
	print('Checking for sprint planning')
	# filter
	sprintplanning_filter = 'Type not in (Test, Sub-task, Epic, "Product Specification", Task) AND (assignee in ' + members + ' OR (assignee in ' + bv_members + '))' + ' AND sprint = ' + sprint_id
	
	print (sprintplanning_filter)

	issues = acc.search_issues(sprintplanning_filter)
	tickets_in_sprint = get_list_issues(issues)
	print('Number of tickets in sprint ' + sprint_num + ': ' + str(len(tickets_in_sprint)))
	print('--------------------')
	print('Have not added to initial page yet')
	workbook = xlsxwriter.Workbook('sprint_planning_' + sprint_num + '.xlsx')
	worksheet = workbook.add_worksheet('sprint_planning')
	bold = workbook.add_format({'bold': True})
	worksheet.write('A1', 'ID', bold)
	worksheet.write('B1', 'Assignee', bold)
	count = 2
	for ticket in tickets_in_sprint:
		if ticket not in data_in_initialPage:
			print(ticket + ' - ' + str(get_assignee_of_issue(ticket)))
			worksheet.write('A'+str(count), ticket)
			worksheet.write('B'+str(count), str(get_assignee_of_issue(ticket)))
			count = count + 1
	workbook.close()

# Retro checking
def Retro_checking():
	print('Get info of issues in sprint ' + sprint_num)
	issues_info = get_issue_info()
	missing_issue = []
	mismatch_issue = []
	print('Retro checking')
	workbook = xlsxwriter.Workbook('retro_' + sprint_num + '.xlsx')
	retro_sheet = workbook.add_worksheet('retro')
	bold = workbook.add_format({'bold': True})
	red_color = workbook.add_format({'font_color': 'red'})
	default_color = workbook.add_format({'font_color': 'black'})
	retro_sheet.write('A1', 'Feature', bold)
	retro_sheet.write('B1', 'Assignee', bold)
	retro_sheet.write('C1', 'Requirements', bold)
	retro_sheet.write('D1', 'Design', bold)
	retro_sheet.write('E1', 'Unit Test', bold)
	retro_sheet.write('F1', 'JUnit', bold)
	retro_sheet.write('G1', 'Functional Test', bold)
	retro_sheet.write('H1', 'Help Update', bold)
	retro_sheet.write('I1', 'Status', bold)
	retro_sheet.write('J1', 'Note', bold)
	
	missing_issue_sheet = workbook.add_worksheet('missing_issue')
	missing_issue_sheet.write('A1', 'ID', bold)
	missing_issue_sheet.write('B1', 'Assignee', bold)
	row = 1
	count_missing = 2
	list_elements = ['Requirements', 'Design', 'Help Update']
	for issue in issues_info:
		dict = {'Requirements': 'F', 'Design': 'F', 'Unit Test': 'F', 'JUnit': 'F', 'Functional Test': 'F', 'Help Update': 'F', 'Status': '', 'Note': ''}
		if issue['Feature'] not in data_in_initialPage:
			missing_issue.append(issue['Feature'])
			missing_issue_sheet.write('A' + str(count_missing), issue['Feature'])
			missing_issue_sheet.write('B' + str(count_missing), str(get_assignee_of_issue(issue['Feature'])))
			count_missing = count_missing + 1
		else:
			col = 0
			print(issue['Feature'])
			retro_sheet.write(row, col, issue['Feature'])
			col = col + 1
			retro_sheet.write(row, col, str(get_assignee_of_issue(issue['Feature'])))
			for k in issue:
				if k != 'Feature':
					print(k + ' - ' + issue[k] + ' - ' + data_in_initialPage[issue['Feature']][k])
					if  k in list_elements:
						link, check = issue[k].split(',')
						if link.lower() == check.lower() and check.lower() == data_in_initialPage[issue['Feature']][k].lower():
							dict[k] = 'T'
					elif issue[k].lower() == data_in_initialPage[issue['Feature']][k].lower():
						dict[k] = 'T'
					print(k + ' : ' + dict[k])
					col = col + 1
					retro_sheet.write(row, col, data_in_initialPage[issue['Feature']][k], default_color if dict[k] == 'T' else red_color)
			print('----------')
			row = row + 1
		
	print('---Missing issues---')
	for issue in missing_issue:
		print(issue + ' - ' + str(get_assignee_of_issue(issue)))
	workbook.close()

user = input('Username: ')
pw = getpass.getpass("Password: ", stream = None)

acc = JIRA('https://jira.renesas.eu', basic_auth = (user, pw))

print('--Login Success--')
print()
type = 0
print('1. Sprint planning')
print('2. Retro')
while True:
	type = input('Sprint planning or Retro? ')
	if type == str(1) or type == str(2):
		break

print()
sprint_num = input("Sprint: ")
sprint_name = 'e2 studio - Sprint ' + sprint_num

sprints = acc.search_issues('Sprint = "' + sprint_name + '"', maxResults = 1)[0].fields.customfield_10004
for sprint in sprints:
    if(sprint_reg.match(sprint)):
        mat = sprint_reg.search(sprint)
        name = mat.group('name')
        if name == sprint_name:
            sprint_id = mat.group('id')
            sprint_startDate = mat.group('startDate')
            sprint_endDate = mat.group('endDate')
            break

print()
			
print('Sprint start date: ', sprint_startDate)
print('Sprint end date: ', sprint_endDate)

print()

# new_sprint_startDate = input("If sprint start date is incorrect, correct it (Press Enter to skip): ")
# if(new_sprint_startDate != ""):
    # sprint_startDate = new_sprint_startDate
# new_sprint_endDate = input("If sprint end date is incorrect, correct it (Press Enter to skip): ")
# if(new_sprint_endDate != ""):
    # sprint_endDate = new_sprint_endDate

print()

# sprint_planning_checking()



print('Get data in initial doc page')

data_in_initialPage = parse_data()

if type == str(1):
	sprint_planning_checking()
elif type == str(2):
	Retro_checking()
print('----END---')
input()