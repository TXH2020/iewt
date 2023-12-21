IEWT(Interactive Embedded Web Terminal)
------------------------------------------

Changes:

- The execution time of commands is recorded even in case of page reload events.
- The application checks if the remote system has tmux installed. Only if installed, tmux is used. Otherwise a normal web terminal is opened. Hence this release is less restrictive.
- Ability to deal with Ctrl+C.
- Additional handlers for test and terminal visualization.
- Separate channel for commands and terminal in WebSocket handler for server to distinguish input. 
- Different datatypes for command results and terminal output for client to distinguish output.
- No logging.
- No requests.
- A file transfer demonstration has been added.
- This release has been thoroughly tested.

Installation:
----------------

- Python 3.8+
- Run ``pip install iewt`` to install iewt package. IEWT requires file creation permissions, hence run in a location with sufficient permissions.
- To run the application you need to have

  1. A remote machine with a Unix(Linux, MacOS etc.) OS.
  2. Tmux installed on the computer/VM.(Optional)
  3. SSH server running on the computer/VM.
  4. Network access to the SSH server.

- Once all the above steps are performed, run the command ``iewt``. Open a browser and goto     `localhost:8888 <http://localhost:8888>`_
- Enter the SSH credentials in the form at the bottom of the screen. The terminal will appear soon after. To automatically execute commands, type the commands in the input field and click on the **send command** button. The command is executed in the terminal and after its completion its time will appear in the readonly input field below the command status button. The command status turns green on success and red on failure.
