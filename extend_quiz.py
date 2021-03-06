import getpass, requests, json, os, sys
import pandas as pd
from termcolor import cprint
from canvasapi import Canvas
from datetime import datetime
import os
from src.helpers import create_instance, _get_course, _get_quiz, _get_students
from src.util import shut_down, print_error, print_success, print_action, continue_quit


mode = "prod" #test

FOLDER = os.path.abspath(os.getcwd())

INPUT = "{}/input".format(FOLDER)
LOGS = "{}/src/log".format(FOLDER)


if mode == "test":
    API_URL = "https://ubc.test.instructure.com/"
else:
    URL = "https://ubc.instructure.com/"
    print(f"Using {URL}...")
    API_URL = URL
    # API_URL = input("Enter Canvas URL instance: ")

# WARNING: Using Ctrl + V for getpass on windows on console seems to cause wonky issues. 
# Not a problem on UI though, only when using console.
# API_KEY = getpass.getpass("Enter Token: ") - getpass on windows
API_KEY = input("Enter Token: ")
# API_KEY = ''
print_success(f'Using URL: {API_URL}')
canvas = create_instance(API_URL, API_KEY)

AUTH_HEADER = {'Authorization': f'Bearer {API_KEY}'}


def dl_quizzes(course_obj):
    '''
    Download list of quizzes in a given course, and puts it into a CSV for users to edit
    Parameters:
        course (canvas.course.Course): Canvas course object from canvasapi
    Returns:
        None. But a CSV is created under input folder called 'quiz_inputs.csv'
    '''
    try:
        quiz_list = course_obj.get_quizzes()
    except Exception as qle:
        shut_down(f'ERROR: Could not find quizzes in course. Please check if quizzes exist.')

    df = pd.DataFrame(columns=['quiz_name','id'])
    for quiz in quiz_list:
        df = df.append({
            'quiz_name': quiz.title,
            'id': quiz.id
            }, ignore_index=True)
    path = os.path.join(INPUT, 'input-all_course_quizzes.csv')
    df.to_csv(path, index=False)



def dl_students(course_id, AUTH_HEADER, API_URL):
    '''
    Create dataframe of students from student list 
    Parameters:
        student_list (json): (created by _get_students)
    Returns:
        None (creates csv from data)
    '''
    student_list = _get_students(course_id, AUTH_HEADER, API_URL)
    #print(student_list)
    # Default for extra_time and extra_attempts is null as requested
    df = pd.DataFrame(student_list)
    df = df[['name','sis_user_id','id']]
    df['extra_time'] = ''
    df['extra_attempts'] =''
    df = df.rename(columns={"sis_user_id": "SIS_id", "id":"canvas_id"})
    df = df[['name','SIS_id','canvas_id','extra_time','extra_attempts']]
    #print(df)
    # df = pd.DataFrame(columns=['name','SIS_id','canvas_id','extra_time','extra_attempts'])
    # for student in student_list:
    #     df = df.append({
    #         'name':student['name'],
    #         'SIS_id': student['sis_user_id'],
    #         'canvas_id': student['id'],
    #         'extra_time': None,
    #         'extra_attempts': None
    #         }, ignore_index=True)
    path = os.path.join(INPUT, 'input-all_course_students.csv')
    df.to_csv(path, index=False)

def extend_quiz_course(course, quiz_id, student_dict):
    return None

def extend_quiz_s(course, quiz_id, student_id, time, attempt):
    '''
    Extend time limit for a given user in a given course taking a given quiz for a specified time
    Parameters:
        course (Canvas.course.Course): Canvas course object from canvasapi
        quiz_id (int): Canvas quiz ID
        student_id (int): Canvas student ID (not SIS ID)
        time (int): minutes of time to be added for quiz
    Returns:
        0 (int): Extension failed
        1 (int): Extension succeeded 
    '''

    # Get Quiz from course
    try:
        quiz = _get_quiz(course, quiz_id)

         # Extend Quiz for given canvas student_id:
        student_dict = {'user_id': student_id, 'extra_time': time, 'extra_attempts': attempt}
        try:
            quiz_extensions = quiz.set_extensions([student_dict])
        except Exception as exe:
            print_error(f'ERROR: Could not extend for student [ID: {student_id}] for quiz [Name: {quiz.title}]. Please check inputs.')
            return 0
    except Exception as exe:
        return 0

    return 1


def extend_quiz_a():
    '''
    Main function of script. 
    Steps are outlined below:
        1. Enter Canvas Course ID, see URL
        2. DL quiz list for course
        3. DL student list for course
        4. Edit inputs CSVs
        5. Confirm input CSVs
        6. Wait for completion
        7. Done
    Parameters: 
        None.
    Returns:
        None.
    '''

    # Test values
    course_id = input("\nEnter your desired Canvas course id: ")
    # course_id = 10751
    
    course = _get_course(canvas, course_id)

    print_action("\nFor first time use on a machine, the following two steps are mandatory.")

    if continue_quit("Do you want to download a Quiz List CSV to edit as input", True):
        print_action("Downloaded Quiz List\nMake sure you edit and save as quiz_input.csv")
        dl_quizzes(course)

    if continue_quit("Do you want to download a Student List CSV to edit as input", True):
        print_action("Downloading Student List\nMake sure you edit and save as student_input.csv")
        dl_students(course_id, AUTH_HEADER, API_URL)
        
    continue_quit("Ensure you have the correct data and files in 'input'. You should have\n\t - quiz_input.csv\n\t - student_input.csv\n\n")
    

    path_a = os.path.join(INPUT, 'student_input.csv')
    path_b = os.path.join(INPUT, 'quiz_input.csv')
        
    
    confirm = False
    while confirm != True:  
        st_df = pd.read_csv(path_a)
        qz_df = pd.read_csv(path_b)
        sys.stdout.write("\r\n{}\n".format(st_df.to_string()))
        sys.stdout.write("\n{}\n".format(qz_df.to_string()))
        sys.stdout.flush()

        confirm = continue_quit("\nPlease confirm that the tables above are correct: ", False)

    print_success("Applying changes to specified quizzes/students...\n")
    # Create Progress Tracker
    x = len(st_df['canvas_id'])
    y = len(qz_df['id'])
    total = x*y
    count = 0
    sys.stdout.write("0/{}".format(total))
    sys.stdout.flush()


    # Create log file
    # dd/mm/YY H:M:S
    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y %H_%M_%S")
    path = os.path.join(LOGS, f'{dt_string}_log.txt')
    log_file = open(path, 'w+')

    log_file.write("Failed Attempts:\n")
    log_file.write("student_id, canvas_id\n")

    status = 0
    for i, student in enumerate(st_df['canvas_id']):
        extra_time = st_df['extra_time'][i]
        extra_attempt = st_df['extra_attempts'][i]

        # If either values are None, set it to 0 to comply with Canvas APU parameter requirements
        if extra_time is None:
            extra_time = 0
        if extra_attempt is None:
            extra_attempt = 0

        for quiz in qz_df['id']:
            status = extend_quiz_s(course, quiz, student, extra_time, extra_attempt)
            count+=1
            sys.stdout.write("\r{}/{}".format(count,total))
            sys.stdout.flush()

            # Log error, failed attempt
            if(status == 0):
                log_file.write(f'{student},{quiz}\n')

    # Close log file, signal completed
    log_file.close()
    print("\nCompleted! Please check file under ./src/log for any failed extensions.")

if __name__ == '__main__':
    extend_quiz_a()
