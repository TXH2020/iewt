IEWT(Interactive Embedded Web Terminal)
------------------------------------------

iewt uses SSH to connect to a remote machine running a Linux OS. It then produces an interactive terminal session upon which the user can execute any command. iewt records the return code as well as the execution time of the entered commands. All these functionalities are available to the user through a web interface. Hence it provides:

- The ability to connect to any remote machine.
- A terminal on a web browser where the user can directly execute commands.
- A simple input field to enter commands which are executed on the terminal upon a button click. 
- An automatically executed command is monitored for its status(success or failure) and completion time. Hence the user can easily analyze the command.
- Suppose there is an event that reloads the webpage. Web terminals and the commands that run in them are usually lost. iewt is not exception. The terminal is lost. However if the commands do not pause for some reason(eg. user input) and are bound to terminate without user intervention(for eg.,ping command doesnt terminate until user presses Ctrl+C), then iewt waits for them to complete, records them and displays the results to the user. This has been made possible using MySQL to record the commands and WebSockets to query the database for results until they are found.
- Prevents user from sending commands for execution when there already is a command executing in the terminal.
- Logging is performed on the browser console and on the server side. Also all the sessions are recorded in a log file(log.txt).

Installation:
----------------

- Run ``pip install iewt`` to install iewt package.
- For enabling the feature related to command execution during event reload, install and run MySQL with username root and no password. To setup the database with the table, use the database script setup.sql provided in the GitHub repo of this project(https://github.com/TXH2020/iewt).
- To test the application you need to have:
1. A computer/VM with a Linux OS.
2. SSH server running on the computer/VM.
3. Network access to the SSH server.

- Once all the above steps are performed, run the command ``iewt``. Open a browser and goto 	`localhost:8888 <http://localhost:8888>`_
- Enter the SSH credentials in the form at the bottom of the screen. The terminal will appear soon after. To automatically execute commands, type the commands in the input field and click on the **send command** button. The command is executed in the terminal and after its completion its time and id will appear in the readonly input fields below the command status button. The command status turns green on success and red on failure.
