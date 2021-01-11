# Quiz Extensions

> - name: quiz-extensions
> - ops-run-with: terminal
> - python>=3.7
> - canvasapi>=2.0.0
> - supports universal environment 🌎

A project that takes input in the form of two CSVs and adds extra time or attempts for students on a list of quizzes.

1. User option to download list of quizzes and students in course
1. List of students with corresponding extra attempts and time to change are entered in `input/student_input.csv`
1. List of quizzes to change for students are entered in `input/quiz_list.csv`
1. Terminal will ask for inputs and confirmations
1. Errors will be shown when necessary by the interface, and failed attempts will be logged in `/src/log` (a log is generated any time the script is run)

## :warning: Important Caveats

- This script only works with **Canvas Classic Quizzes**
- The attempt and time extensions will be overwritten when you run this script (does not add extra attempts or time, replaces them)
- The script assumes that you want to extend the time and/or attempts for each student for each quiz listed
- We have not tested the behaviour of this script for non-published or past-due quizzes

## To Run

> Are you Sauder LS Ops? Refer to the instructions [here](https://github.com/saud-learning-services/instructions-and-other-templates) but note that this project is only runnable via terminal for the time being.

For more detailed instructions see [Detailed Instructions](detailed_instructions.md)

### First Time

You will need to create the quiz_extension environment. We use conda to manage our projects.
`$ conda env create -f environment.yml`

### Every Time

1. `$ conda activate quiz_extension`
1. `$ python extend_quiz.py`

### Inputs for Required

1. Canvas API Token
1. Canvas Course ID
1. Student and Quiz CSVs

---

## Acknowledgement :star2:

This adapatation was forked from https://github.com/ubccapico/quiz-extension where the original author acknowledgements were:

> ### Author
>
> - **Tyler Cinkant** - [Lannro](https://github.com/Lannro)
