IEWT(Interactive Embedded Web Terminal)
------------------------------------------

This release provides several improvements over the previous ones.

- Tmux has been integrated with the application. All terminals will hence be created upon tmux. This provides a lot of advantages:

  1. The terminals as well as the commands that run on it are preserved in the events of page reload. Also, the application tracks commands for status and time even in the case of a reload.
  2. No need for a database server. Hence the application is simpler to configure and also lighter.
  3. Frontend is simplified since command id need not be explicitly maintained for command tracking.
  4. There is no need to prevent sessions from closing immediately(to preserve commands during reload events). Hence the application is more flexible and simpler.

- The logging has been improved. A separate logs directory will be created. One log per terminal session will be created in the logs directory.
- No logging is made on the browser console to prevent clogging by unnecessary messages.
- The application makes a post request with all command information to a server on port 5000 on localhost(only if it is available). Hence, the other server can be primarily used to store command information for future analysis or other purposes and its implementation is completely left to the user. This is suitable for a MicroServices setup for optional analysis. The app first checks if the server is alive by pinging localhost:5000/test. If successful, it makes post requests to localhost:5000/command.
- The microservices setup is further strengthened by the attempt to abstract several functions from the backend to the frontend. For example, the special commands(script,exit) are checked in the frontend instead of the backend. The frontend also generates an internal command id which the backend generated previously. The backend is only responsible for the terminals, command execution and tracking of commands.

Note: The command execution time obtained in the case of reload events is the time between the restoration of the terminal and the retrieval of the status and not the actual execution time.

Installation:
----------------

- Run ``pip install iewt`` to install iewt package.
- To test the application you need to have

  1. A computer/VM with a Unix(Linux, MacOS etc.) OS.
  2. Tmux installed on the computer/VM.
  3. SSH server running on the computer/VM.
  4. Network access to the SSH server.

- Once all the above steps are performed, run the command ``iewt``. Open a browser and goto     `localhost:8888 <http://localhost:8888>`_
- Enter the SSH credentials in the form at the bottom of the screen. The terminal will appear soon after. To automatically execute commands, type the commands in the input field and click on the **send command** button. The command is executed in the terminal and after its completion its time will appear in the readonly input field below the command status button. The command status turns green on success and red on failure.
