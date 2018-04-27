""" 
Xander's code for converting csv to Andy's format
NOTE: REQUIRES A DATA.CSV FILE IN THE DIRECTORY THE PROGRAM IS RUN IN 
Obtain this by downloading the second sheet on the results form as .csv, 
renaming it, and placing it appropriately next to the .py file

"""
from random import choice
from random import randint
import random
import subprocess,os
import shutil
import csv
import string
import operator
import sqlite3

AMOUNT_OF_QUESTIONS = 39 # Includes multiple choice questions, plus name and gender
PRINT_REPORT = False

render_data = [] # Collection of calculated data to pass to rendering
guys = []
chicks = [] # Eventual storage of reformatted data
MALE = "MALE"
FEMALE = "FEMALE"

class Person:
	def __init__(self):
		self.first_name = "BOB"
		self.last_name = "EVANS"
		self.sex = "SAUSAGE"
		self.answers = []
		self.grade = 10
		self.id = -1
		self.matches = {}
		self.date_matches = []
		self.friend_matches = []
		self.avg_rank = 0
		self.avg_score = 0
		
	def from_row(self, row):
		self.id = row[0]
		self.first_name = row[1]
		self.last_name = row[2]
		self.sex = row[3]
		self.grade = row[4]
		
	def save_student(self, db):
		if self.id < 0:
			student_cmd = """
			INSERT OR REPLACE INTO students
			(fname, lname, sex, grade) VALUES
			(:fname, :lname, :sex, :grade);"""
		
			
			db.execute(student_cmd,	{ 
				"fname":self.first_name,
				"lname":self.last_name,
				"sex":1 if self.sex == MALE else 2,
				"grade":self.grade})
			self.id = db.lastrowid
		else:
			student_cmd = """
			INSERT OR REPLACE INTO students
			(id, fname, lname, sex, grade) VALUES
			(:id, :fname, :lname, :sex, :grade);"""
		
			
			db.execute(student_cmd,	{ 
				"id":self.id,
				"fname":self.first_name,
				"lname":self.last_name,
				"sex":1 if self.sex == MALE else 2,
				"grade":self.grade})
			
				
	def save_answers(self, db):
		answers_cmd = """
		INSERT OR REPLACE INTO answers
		(student_id, question_id, value) VALUES
		(:student_id,:question_id,:value);"""
		
		question_id = 0
		for answer in self.answers:
			db.execute(answers_cmd,{
				"student_id":self.id,
				"question_id":question_id,
				#"value":"ABCD".index(answer)})
				"value":answer}) # Attempt to patch non-labeled question issues
			question_id+=1


class RenderData:
	def __init__(self,target,top_matches,friend_matches,least_compatible_matches):
		self.target = target
		self.top_matches = top_matches
		self.friend_matches = friend_matches
		self.least_compatible_matches = least_compatible_matches


class Match:
	def __init__(self):
		self.person = Person()
		self.owner = Person()
		self.score = 0.0
		self.friend_mode = False
		self.rank = 0
		
	def compare(matchA, matchB):
		if matchA.score > matchB.score:
			return -1
		if matchA.score == matchB.score:
			return 0
		if matchA.score < matchB.score:
			return 1


db_create = ["""CREATE TABLE IF NOT EXISTS students
( id INTEGER PRIMARY KEY AUTOINCREMENT, fname text, lname text, sex integer, grade integer);""",

"""CREATE TABLE IF NOT EXISTS answers
( student_id integer, question_id integer, value str);""" ]


def get_fudge():
	return 0
	upper = (1./(AMOUNT_OF_QUESTIONS+1))/2
	fudge = (random.random())*upper
	# print "{:3.4f}".format(fudge)
	return fudge


def opendb(in_memory):
	con = sqlite3.connect(":memory:" if in_memory else "matchmaker.db")
	con.text_factory = str
	cur = con.cursor()
	for cmd in db_create:
		cur.execute(cmd)
	return cur


def sanitize_name_list(name_list):
	length = len(name_list)
	for index in range(length):
		name = name_list[index]
		name = name.split()[0]
		name_list[index] = name


def random_data_generator(number_of_men = 200, number_of_women = 200, number_of_questions = 22, answers=['A','B','C','D']):
	man_names = open("census-dist-male-first.txt","r").readlines()
	sanitize_name_list(man_names)
	woman_names = open("census-dist-female-first.txt","r").readlines()
	sanitize_name_list(woman_names)
	last_names =open("census-dist-2500-last.txt","r").readlines()
	sanitize_name_list(last_names)
	people = []
	for random_guy in range(number_of_men):
		man = Person()
		man.first_name = choice(man_names)
		man.last_name = choice( (
			choice(man_names+woman_names)+"SSON", 
			choice(last_names)))
		man.sex = MALE
		man.answers =[choice(answers) for i in range(number_of_questions)]
		people.append(man)
	for random_chick in range(number_of_women):
		woman = Person()
		woman.first_name = choice(woman_names)
		woman.last_name = choice((
			choice(man_names+woman_names)+"DOTTIR", 
			choice(last_names)))
		woman.sex = FEMALE
		woman.answers =[choice(answers) for i in range(number_of_questions)]
		people.append(woman)
	return people

# Assumes format of:
# Timestamp, Email, Gender, Grade, Questions

def cleanse():
	try:
		os.remove("cleandata.csv")
	except OSError:
		pass
	responses = []
	max_question_index = 0
	with open("data.csv", "r") as csvfile:
		scanner = csv.reader(csvfile, delimiter=',')
		for row in scanner:
			response = {}
			email = row[1]
			period = email.find('.')
			at = email.find('@')
			response["fname"] = (email[0:period]).capitalize()
			response["lname"] = (email[period+1:at]).capitalize()
			response["gender"] = row[2]
			response["grade"] = row[3]
			for i in range(4,len(row)):
				response[str(i)] = row[i]
				if i > max_question_index:
					max_question_index = i
			responses.append(response)
	with open("cleandata.csv", 'w') as csvfile:
		fieldnames = ["fname","lname","gender","grade"]
		if i != 0:
			for i in range(4,max_question_index+1):
				fieldnames.append(str(i))
		writer = csv.DictWriter(csvfile,fieldnames=fieldnames)
		for response in responses[1:]:  # Begins at one to avoid gross header line
			writer.writerow(response)
	csvfile.close()
def load():
	last_names =open("census-dist-2500-last.txt","r").readlines()
	sanitize_name_list(last_names)
	with open("cleandata.csv", "r") as csvfile:
		scanner = csv.reader(csvfile, delimiter=',')
		persons = []
		men = []
		women = []
		contains_email = False
		offset = 0
		for row in scanner: # Loops through rows read from csv file
			row_person = Person()
			
			if row[1].find("@")>0: # looking for emails
				contains_email = True
			
			if contains_email is False:
				row_person.first_name = row[0]
				row_person.last_name = row[1]
				row_person.grade = row[3]
				
				if row[2].upper() == MALE:
					row_person.sex = MALE
				else:
					row_person.sex = FEMALE

				offset = 4
			else:
				time = row[0] # Is this correct???
				email = row[1]
				row_person.first_name = row[2]
				row_person.last_name = row[3]
				row_person.grade = row[4]
				
				if row[5].upper() == MALE:
					row_person.sex = MALE
				else:
					row_person.sex = FEMALE
				
				offset = 6
				
			
			additionList = []
			AMOUNT_OF_QUESTIONS = len(row) - offset - 1
			for i in range(offset,len(row)): # Puts multiple choice answers into a list
				additionList.append(row[i][:1])
			row_person.answers = additionList
			
			persons.append(row_person)
		return persons


def clamp(value):
	if value > 100:
		return 100
	elif value < 0:
		return 0
	else:
		return value

		
def report(person, date_matches, friend_matches):
	if True: #PRINT_REPORT:
		print ("PERSON: {fname} {lname}".format(
			fname=person.first_name,
			lname=person.last_name))
		print("---------------------")
		print ("Dates:")
		for date_match in date_matches:
			print("{score:3.2%} {fname} {lname}".format(
				score=date_match.score,
				fname=date_match.person.first_name,
				lname=date_match.person.last_name))
		print("---------------------")
		print("Friends:")
		for friend_match in friend_matches:
			print("{score:3.2%} {fname} {lname}".format(
				score=friend_match.score,
				fname=friend_match.person.first_name,
				lname=friend_match.person.last_name))
		print("\n\n")
	return


# JINJA:
from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('match', 'templates'))


def master_report(data):
	if not os.path.exists("output"):
		os.mkdir("output")
	if not os.path.exists("output/primary"):
		os.mkdir("output/primary")
	shutil.copy("templates/pure-min.css","output/primary/pure-min.css")
	template = env.get_template('report_template.html')
	html = template.render(data=data)
	out = open("output/primary/master.html","w")
	out.write(html)
	
	out.close()
	

def html_report(target, top_matches, friend_matches, least_compatible_matches): # Outdated and unused

	if not os.path.exists("output"):
		os.mkdir("output")
	if not os.path.exists("output/primary"):
		os.mkdir("output/primary")
	shutil.copy("templates/pure-min.css","output/primary/pure-min.css")
	template = env.get_template('report_template.html')
	student_data = []
	data = RenderData(target=target,top_matches=top_matches,
		friend_matches=friend_matches,
		least_compatible_matches=least_compatible_matches)
	student_data.append(data)
	html = template.render(
		data=student_data)
	out = open(
		"output/primary/{lname}_{fname}.html".format(
			lname=target.last_name,
			fname=target.first_name),"w")
	out.write(html)
	
	out.close()

def oddball_report(target, students, stats):

	if not os.path.exists("output"):
		os.mkdir("output")
	if not os.path.exists("output/oddball"):
		os.mkdir("output/oddball")
		
	shutil.copy("templates/pure-min.css","output/oddball/pure-min.css")
	template = env.get_template('oddball_report_template.html')

	avg_rank = target.avg_rank
	avg_score = target.avg_score
	

	html = template.render(
		target=target,
		students=students,
		avg_rank=avg_rank,
		avg_score=avg_score,
		best_date_matches=stats["best_date_matches"],
		worst_date_matches = stats["worst_date_matches"],
		best_friend_matches = stats["best_friend_matches"],
		worst_friend_matches = stats["worst_friend_matches"])
	out = open(
		"output/oddball/{lname}_{fname}.html".format(
			lname=target.last_name,
			fname=target.first_name),"w")
	out.write(html)
	out.close()



	
def rawSQL(string):
	db.execute(string)
	rows = db.fetchall()
	return rows

def student_query(db, student, sex=MALE, limit=10, isDescending=True):
	"""
	This query returns matches for a student with a given sex, limit and ordering 
	"""
	
	cmd = """
	SELECT a1.student_id as a1id, a2.student_id as a2id, s.grade, COUNT(*) as score
		FROM answers AS a1
		INNER JOIN answers as a2 
			ON a1.student_id IS NOT a2.student_id AND a1.question_id IS a2.question_id AND a1.value IS a2.value  
		INNER JOIN students as s
			ON s.id IS a2.student_id
		WHERE s.sex IS :sex AND a1id IS :student_id
		GROUP BY a2.student_id
		ORDER BY a1id, score DESC
		LIMIT :limit
		"""
		
	db.execute(cmd,	{ 
		"student_id":student.id,
		"sex" : 1 if sex is MALE else 2,
		"limit":limit,
		"direction":"DESC" if isDescending else "ASC" }	)
		
	rows = db.fetchall()
	
	return rows
	
	
	
def master_query(db):
	"""
	This query returns every match for every student within the database
	"""
	
	cmd = """
	SELECT a1.student_id as a1id, a2.student_id as a2id, COUNT(*) as score
		FROM answers AS a1
		INNER JOIN answers as a2 
			ON a1.student_id IS NOT a2.student_id AND a1.question_id IS a2.question_id AND a1.value IS a2.value  
		INNER JOIN students as s
			ON s.id IS a2.student_id
		GROUP BY a2.student_id, a1.student_id
		"""
		
	db.execute(cmd)
		
	rows = db.fetchall()
	
	return rows
	
	
def get_student(id):
	"""
	This query returns a row representing a student with the given id
	"""
	
	db.execute("SELECT * FROM students WHERE id = :id",{"id":id})
	first = db.fetchone()
	return first
	
def parse_main_query_rows(rows, students={}):
	"""
	This takes the output from our master_query and yields populated
	People (student) objects with matches. It also computes some basic
	global statistics for my own amusement.
	"""
	avg_score = 0
	most_popular = None
	most_compatible = None
	matches = []
	friend_matches = []
	date_matches = []
	
	for row in rows:
		a1_id = row[0]
		a2_id = row[1]
		score = row[2]
		
		if a1_id not in students:
			a1_student = Person()
			a1_student.from_row(get_student(a1_id))
			students[a1_id] = a1_student
		else:
			a1_student = students[a1_id]
		
		if a2_id not in students:
			a2_student = Person()
			a2_student.from_row(get_student(a2_id))
			students[a2_id] = a2_student
		else:
			a2_student = students[a2_id]
		
		match = Match()
		match.owner = a1_student
		match.person = a2_student
		match.score = score * 1.0 / AMOUNT_OF_QUESTIONS
		matches.append(match)
		
		a1_student.matches[a2_id] = match
		if a1_student.sex != a2_student.sex:
			a1_student.date_matches.append(match)
			date_matches.append(match)
		else:
			a1_student.friend_matches.append(match)
			friend_matches.append(match)
		
	for key in students:
		student = students[key]
		student.date_matches = sorted(student.date_matches,cmp=Match.compare)
		student.friend_matches = sorted(student.friend_matches,cmp=Match.compare)
		
		# You are my Index[0] Baby!
		
		for match in student.date_matches:
			match.rank = student.date_matches.index(match)+1
		for match in student.friend_matches:
			match.rank = student.friend_matches.index(match)+1
		
		
		for key in student.matches:
			match = student.matches[key]
			student.avg_rank += match.rank
			student.avg_score += match.score
			
		student.avg_rank /= (len(students)-1)
		student.avg_score /= (len(students)-1)
		avg_score += student.avg_score
		
		if most_popular is None:
			most_popular = student
		else:
			if most_popular.avg_rank < student.avg_rank:
				most_popular = student
		if most_compatible is None:
			most_compatible = student
		else:
			if most_compatible.avg_score < student.avg_score:
				most_compatible = student
	best_friend_match = None
	for match in friend_matches:
		if best_friend_match is None:
			best_friend_match = match
		elif match.score > best_friend_match.score:
			best_friend_match = match
	best_date_match = None
	for match in date_matches:
		if best_date_match is None:
			best_date_match = match
		elif match.score > best_date_match.score:
			best_date_match = match
	avg_score /= len(students)

	friend_matches.sort(key=lambda x: x.score,reverse=True)
	date_matches.sort(key=lambda x: x.score,reverse=True)

	best_friend_matches = friend_matches[:20]
	best_date_matches = date_matches[:20]

	friend_matches.sort(key=lambda x: x.score,reverse=False)
	date_matches.sort(key=lambda x: x.score,reverse=False)

	worst_friend_matches = friend_matches[:20]
	worst_date_matches = date_matches[:20]

	i=0
	while i < len(best_friend_matches):
		match1 = best_friend_matches[i]
		for match2 in best_friend_matches:
			repeat = False
			if match1.owner == match2.person:
				if match1.person == match2.owner:
					repeat = True
			if repeat:
				best_friend_matches.remove(match2)
		i+=1
	i=0
	while i < len(worst_friend_matches):
		match1 = worst_friend_matches[i]
		for match2 in worst_friend_matches:
			repeat = False
			if match1.owner == match2.person:
				if match1.person == match2.owner:
					repeat = True
			if repeat:
				worst_friend_matches.remove(match2)
		i+=1
	i=0
	while i < len(worst_date_matches):
		match1 = worst_date_matches[i]
		for match2 in worst_date_matches:
			repeat = False
			if match1.owner == match2.person:
				if match1.person == match2.owner:
					repeat = True
			if repeat:
				worst_date_matches.remove(match2)
		i+=1
	i=0
	while i < len(best_date_matches):
		match1 = best_date_matches[i]
		for match2 in best_date_matches:
			repeat = False
			if match1.owner == match2.person:
				if match1.person == match2.owner:
					repeat = True
			if repeat:
				best_date_matches.remove(match2)
		i+=1
	best_friend_matches.sort(key=lambda x: x.score,reverse=True)
	best_date_matches.sort(key=lambda x: x.score,reverse=True)
	worst_friend_matches.sort(key=lambda x: x.score,reverse=False)
	worst_date_matches.sort(key=lambda x: x.score,reverse=False)
	best_date_matches = best_date_matches[:10]
	best_friend_matches = best_friend_matches[:10]
	worst_date_matches = worst_date_matches[:10]
	worst_friend_matches = worst_friend_matches[:10]
	return students, { 
		"avg_score":avg_score,
		"most_compatible": most_compatible,
		"most_popular": most_popular,
		"best_date_match": best_date_match,
		"best_friend_match": best_friend_match,
		"best_friend_matches": best_friend_matches,
		"best_date_matches": best_date_matches,
		"worst_friend_matches": worst_friend_matches,
		"worst_date_matches": worst_date_matches
	}
	
		
		
def do_html_report(students):
	"""
	This renders out the "Primary" report html docs, calling the
	html_report(...) render function on each student in the list:
	`students`
	"""
	for student in students:
		date_list = student.date_matches[:10]
		friend_list = student.friend_matches[:10]
		temp = [] + student.date_matches
		temp.reverse()
		dislike_list = temp[:3]
		html_report(student,date_list,friend_list,dislike_list)
		data = RenderData(target=student,top_matches=date_list,
			friend_matches=friend_list,
			least_compatible_matches=dislike_list)
		render_data.append(data)
		
	render_data.sort(key=lambda datum: datum.target.last_name)
	# Alphabetize render data entries by last name to make report prettier
		
	
	master_report(render_data)
	# Move html_report stuff to another function
	#do_master_report(master_uber_mega_ultra_awesome_list)
	
if __name__ == "__main__":
	db = opendb(False) # make False to save db to disk
	print ("Cleansing data...\n")
	cleanse()
	print ("When you are sure all names are properly formatted, enter 'y' to proceed.\n")
	path = "cleandata.csv"

	if os.name == 'nt':
		os.startfile(path)
	elif sys.platform.startswith('darwin'):
		subprocess.call(('open',path))
	elif os.name == 'posix':
		subprocess.call(('xdg-open',path))
	if raw_input("Make any changes now. Ready to proceed? (y/n): ") == "y":
		pass
	else:
		print "Execution aborted."
		exit()
	print ("Loading data...\n")
	#ugly_people,guys,chicks = random_data_generator()
	file_people = load()
	
	for person in file_people: # Store File-People in the Database
		person.save_student(db)
		person.save_answers(db)
		
	file_people = None

	print ("Finding Matches...\n")

	students = {}
	rows = master_query(db)
	students, stats = parse_main_query_rows(rows, students)
	
	print("Statistics:")
	print("Average Score: {avg_score}".format(avg_score=stats["avg_score"]))
	print("Most Popular: {fname} {lname}".format(
		fname = stats["most_popular"].first_name, 
		lname = stats["most_popular"].last_name))
		
	print("Most Compatible: {fname} {lname}".format(
		fname = stats["most_compatible"].first_name, 
		lname = stats["most_compatible"].last_name))
	print("")

	print("Best couple: {fname1} {lname1} and {fname2} {lname2} with {score}%".format(
		fname1 = stats["best_date_match"].owner.first_name,
		lname1 = stats["best_date_match"].owner.last_name,
		fname2 = stats["best_date_match"].person.first_name,
		lname2 = stats["best_date_match"].person.last_name,
		score = stats["best_date_match"].score*100)
	)
	print("Best friends: {fname1} {lname1} and {fname2} {lname2} with {score}%".format(
		fname1 = stats["best_friend_match"].owner.first_name,
		lname1 = stats["best_friend_match"].owner.last_name,
		fname2 = stats["best_friend_match"].person.first_name,
		lname2 = stats["best_friend_match"].person.last_name,
		score = stats["best_friend_match"].score*100)
	)
	print("")
	for match in stats["best_friend_matches"]:
		print("Friend match: {fname1} {lname1} and {fname2} {lname2} with {score}%".format(
			fname1 = match.owner.first_name,
			lname1 = match.owner.last_name,
			fname2 = match.person.first_name,
			lname2 = match.person.last_name,
			score = match.score*100)
		)
	for match in stats["best_date_matches"]:
		print("Date match: {fname1} {lname1} and {fname2} {lname2} with {score}%".format(
			fname1 = match.owner.first_name,
			lname1 = match.owner.last_name,
			fname2 = match.person.first_name,
			lname2 = match.person.last_name,
			score = match.score*100)
		)
	for match in stats["worst_friend_matches"]:
		print("Unlikely friend match: {fname1} {lname1} and {fname2} {lname2} with {score}%".format(
			fname1 = match.owner.first_name,
			lname1 = match.owner.last_name,
			fname2 = match.person.first_name,
			lname2 = match.person.last_name,
			score = match.score*100)
		)
	for match in stats["worst_date_matches"]:
		print("Unlikely date match: {fname1} {lname1} and {fname2} {lname2} with {score}%".format(
			fname1 = match.owner.first_name,
			lname1 = match.owner.last_name,
			fname2 = match.person.first_name,
			lname2 = match.person.last_name,
			score = match.score*100)
		)
	print("")

	print ("Caching Results...\n")
	student_list = []
	for key in students:
		student_list.append(students[key])
		
	
	print ("Writing Primary Report\n")
	do_html_report(student_list)
	
	print ("Writing Oddball Reports")
	for person in student_list:
		oddball_report(person, student_list, stats)
