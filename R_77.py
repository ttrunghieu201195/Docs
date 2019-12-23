from jira import JIRA
import getpass
import re

# Options setting
velocity = 10
version = '"e2 studio 7.8"'
end_sprint = 113
version_startDate = '"2019-11-25"'
version_endDate = '"2020-02-14"'
members = '(chinh.nguyen.ym, hieu.tran.eb, nam.nguyen.te, nguyen.duong.uw, phuong.nguyen.px, van.tran.yg, vien.nguyen.uj, trieu.truong-dang.banvien, tien.truong-hoang.banvien, vinh.luong.xz, hoang.nguyen.te, thuan.dao.fz, nhat.than.zy)'
bv_members = '(huy.tran-quockhang.banvien, son.nguyen.banvien)'
headCount = 9

def getIssues(filter):
    return acc.search_issues(filter, maxResults = 1000)

def calculateStorypoint(issues):
    totalStorypoints = 0
    for issue in issues:
        if (type(issue.fields.customfield_10002) is float):
            totalStorypoints = totalStorypoints + issue.fields.customfield_10002
    return totalStorypoints

def removed_issue_in_sprint(sprint):
    removed_issues = acc.removed_issues(93,sprint)
    removed_issues_filter = 'issueKey in ('
    for issue in removed_issues:
        removed_issues_filter = removed_issues_filter + (str(issue)) + ','
    if removed_issues:
        removed_issues_filter = removed_issues_filter[:-1]
        removed_issues_filter = removed_issues_filter + ') AND Type not in (Test, Sub-task, Epic, "Product Specification", "Change Control") AND (assignee was in ' + members + ' ON "' + sprint_startDate + '" OR (assignee was in ' + bv_members + ' ON "' + sprint_startDate + '" AND labels = BV_Debugger))' + reopen_filter
        return getIssues(removed_issues_filter)
    else:
        return []

def get_list_filter(issues):
    filter = 'issueKey in ('
    for issue in issues:
        filter = filter + (str(issue)) + ','
    return filter[:-1] + ')'

def remove_issues_containing_many_affected_versions(issues):
    copied_issues = issues[:]
    for issue in issues:
        if len(issue.fields.versions) > 1:
            copied_issues.remove(issue)
    return copied_issues

sprint_reg = re.compile('.*id=(?P<id>[0-9]+).*name=(?P<name>[^,]+).*startDate=(?P<startDate>[^T]+).*endDate=(?P<endDate>[^T]+).*', flags=re.S)

user = input("Username: ")
pw = getpass.getpass("Password: ", stream = None)

acc = JIRA('https://jira.renesas.eu', basic_auth = (user, pw))

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

new_sprint_startDate = input("If sprint start date is incorrect, correct it (Press Enter to skip): ")
if(new_sprint_startDate != ""):
    sprint_startDate = new_sprint_startDate
new_sprint_endDate = input("If sprint end date is incorrect, correct it (Press Enter to skip): ")
if(new_sprint_endDate != ""):
    sprint_endDate = new_sprint_endDate

print()

reopen_filter = ' AND (Type in (Test, Sub-task, Epic, "Product Specification", Task, "Change Control") OR status was in (Verification, Resolved, Duplicate, Invalid, "Won\'t Fix", Done) ON "' + sprint_startDate + '" OR status was not Reopened DURING ("' + sprint_startDate + '", "' + sprint_endDate + '"))'

#Story points of issues removed from Sprint
removed_issues_story_points = calculateStorypoint(removed_issue_in_sprint(sprint_id))

#Story points of incompleted issues of Sprint
filter = 'Type not in (Test, Sub-task, Epic, "Product Specification", "Change Control") AND (assignee was in ' + members + ' ON "' + sprint_endDate + '" OR (assignee was in ' + bv_members + ' ON "' + sprint_endDate + '" AND labels = BV_Debugger)) AND sprint = ' + sprint_id + ' AND status was not in (Verification, Resolved, Duplicate, Invalid, "Won\'t Fix", Done) ON "' + sprint_endDate + '"' + reopen_filter
incompleted_issues_story_points = calculateStorypoint(getIssues(filter))

#Story points of issues added to Sprint after Sprint start
filter = 'Type not in (Test, Sub-task, Epic, "Product Specification", "Change Control") AND (assignee in ' + members + ' OR (assignee in ' + bv_members + ' AND labels = BV_Debugger)) AND issueFunction in addedAfterSprintStart("e2 studio Scrum", "' + sprint_name + '") AND Sprint = ' + sprint_id + reopen_filter
added_issues_story_points = calculateStorypoint(getIssues(filter))

#Story points of issues of Sprint at the end of Sprint
filter = 'Type not in (Test, Sub-task, Epic, "Product Specification", "Change Control") AND (assignee was in ' + members + ' ON "' + sprint_endDate + '" OR (assignee was in ' + bv_members + ' ON "' + sprint_endDate + '" AND labels = BV_Debugger)) AND Sprint = ' + sprint_id + reopen_filter
issues_story_points = calculateStorypoint(getIssues(filter))

#Story points of completed issues at the end of Sprint
filter = 'Type not in (Test, Sub-task, Epic, "Product Specification", "Change Control") AND (assignee was in ' + members + ' ON "' + sprint_endDate + '" OR (assignee was in ' + bv_members + ' ON "' + sprint_endDate + '" AND labels = BV_Debugger)) AND sprint = ' + sprint_id + ' AND status was in (Verification, Resolved, Duplicate, Invalid, "Won\'t Fix", Done) ON "' + sprint_endDate + '"' + reopen_filter
completed_issues_story_points = calculateStorypoint(getIssues(filter))

#Story Points of the backlog
filter = 'Type not in (Test, Sub-task, Epic, "Product Specification", "Change Control") AND (assignee in ' + members + ' OR (assignee in ' + bv_members + ' AND labels = BV_Debugger)) AND fixVersion = ' + version
backlog_issues = getIssues(filter)
backlog_issues_story_points = calculateStorypoint(backlog_issues)

#Story points of incompleted issues of backlog
filter = 'Type not in (Test, Sub-task, Epic, "Product Specification", "Change Control") AND (assignee in ' + members + ' OR (assignee in ' + bv_members + ' AND labels = BV_Debugger)) AND fixVersion = ' + version + ' AND status was not in (Verification, Resolved, Duplicate, Invalid, "Won\'t Fix", Done) ON "' + sprint_endDate + '"'
backlog_incompleted_issues_story_points = calculateStorypoint(getIssues(filter))

print('***Percentage of incomplete issues from a Sprint***')
print(removed_issues_story_points)
print(incompleted_issues_story_points)
print(issues_story_points)
print(completed_issues_story_points)
print(max(0.0, (removed_issues_story_points + incompleted_issues_story_points - added_issues_story_points) / issues_story_points * 100.0), '%')
print()

print('***Average number of story points per developer completed (Velocity)***')
print(completed_issues_story_points / headCount)
print()

print('***Percentage of new items added in a Sprint (Change in a sprint)***')
print(added_issues_story_points / issues_story_points * 100.0, '%')
print()

filter = 'Type not in (Test, Sub-task, Epic, "Product Specification", Task, "Change Control") AND (assignee was in ' + members + ' DURING ("' + sprint_startDate + '", "' + sprint_endDate + '") OR (assignee was in ' + bv_members + ' DURING ("' + sprint_startDate + '", "' + sprint_endDate + '") AND labels = BV_Debugger)) AND status changed to Reopened DURING ("' + sprint_startDate + '", "' + sprint_endDate + '")'
issues = getIssues(filter)
print('***Number of re-opened tickets from a previous sprint (Quality measure)***')
print(get_list_filter(issues))
print(len(issues))
print()

filter = '"Detection Stage" = Customer AND Type = Bug AND (assignee in ' + members + ' OR (assignee in ' + bv_members + ' AND labels = BV_Debugger)) AND (created >= ' + version_startDate + ' AND created <= ' + version_endDate + ')'
issues = getIssues(filter)
print('***Customer issue count (KPI measure but track from Sprint to Sprint)***')
print(get_list_filter(issues))
print(len(issues))
print()

filter = 'Type not in (Test, Sub-task, Epic, "Product Specification", "Change Control") AND (assignee in ' + members + ' OR (assignee in ' + bv_members + ' AND labels = BV_Debugger)) AND fixVersion = ' + version
print('***Total Story Points of the backlog***')
print(backlog_issues_story_points)
print()

filter = 'Type not in (Test, Sub-task, Epic, "Product Specification", "Change Control") AND (assignee in ' + members + ' OR (assignee in ' + bv_members + ' AND labels = BV_Debugger)) AND fixVersion = ' + version + ' AND "Story Points" = empty AND status was not in (Verification, Resolved, Duplicate, Invalid, "Won\'t Fix", Done)'
issues = getIssues(filter)
print('***Number of non-estimated issues (Ensure we can track backlog completion status)***')
print(get_list_filter(issues))
print(len(issues))
print(100.0 * len(issues) / len(backlog_issues), '%')
print()

filter = 'Type = Bug AND (assignee in ' + members + ' OR (assignee in ' + bv_members + ' AND labels = BV_Debugger)) AND fixVersion = ' + version + ' AND ((affectedVersion = ' + version + ') OR (affectedVersion is EMPTY)) AND status not in (Duplicate, Invalid)'
numberOfBugIssues1 = len(remove_issues_containing_many_affected_versions(getIssues(filter)))
filter = 'Type = Bug AND (assignee in ' + members + ' OR (assignee in ' + bv_members + ' AND labels = BV_Debugger)) AND fixVersion = ' + version + ' AND status not in (Duplicate, Invalid)'
numberOfBugIssues2 = len(getIssues(filter))
print('***Bug ratio count (Measure ratio of improvements versus in process bugs)***')
print(numberOfBugIssues1 / numberOfBugIssues2 * 100.0, '%')
print()

print('***Number of story points over estimation against team capacity***')
print(backlog_incompleted_issues_story_points - velocity * headCount * (end_sprint - int(sprint_num)))
print()