IEWT(Interactive Embedded Web Terminal)
------------------------------------------

This release provides approximate execution time(as opposed to the previous versions which gave exact time). The small sacrifice made in the accuracy of measurement of the execution time gives a lot of benefits in return because:

- it allows us to execute commands like cd which changes the directory of the embedded terminal which want possible before.
- it allow us to retain environment variables of the terminal session.
- the time command was used to measure the exact execution time. This made the application somewhat specific to a Linux OS. However, with the removal of time command, the application can now connect to a wider variety of machines. The only requirement is a Unix based OS(Linux, MacOS etc).
- An additional feature for local storage clearance(only in case of error) has been provided. 
- Logging has been improved. 
- a special treatment of script(used to log terminal sessions) command has been made so that the system does not await the status of script command and hence only execute the command and not provide the status. This means that the script command can now be executed from the input.

Installation:
----------------

- Run ``pip install iewt`` to install iewt package.
- For enabling the feature related to command execution during event reload, install and run MySQL with username root and no password. To setup the database with the table, use the database script setup.sql provided in the GitHub repo of this project(https://github.com/TXH2020/iewt).
- To test the application you need to have

  1. A computer/VM with a Unix(Linux, MacOS etc.) OS.
  2. SSH server running on the computer/VM.
  3. Network access to the SSH server.

- Once all the above steps are performed, run the command ``iewt``. Open a browser and goto 	`localhost:8888 <http://localhost:8888>`_
- Enter the SSH credentials in the form at the bottom of the screen. The terminal will appear soon after. To automatically execute commands, type the commands in the input field and click on the **send command** button. The command is executed in the terminal and after its completion its time and id will appear in the readonly input fields below the command status button. The command status turns green on success and red on failure.
