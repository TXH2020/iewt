//check whether there is a command pending
var special_comm_flag=0;
//special commands list
var spec_commands=['script','exit']
//perform sendmessage when button is clicked
var button = document.querySelector("#sendMessage");
function sendMessage() 
{
    var command = document.querySelector("#message").value;
    if(command.search('\\S')===-1)
    	alert("Empty command. Please enter a valid command");
    else{
    	const iframe = document.querySelector("iframe");
    	//generate an id for distinguishing commands
    	var id=''
    	for(var i=0;i<13;i++)
    		id+=Math.floor(Math.random()*10);
    	//check if command is special.
    	for(var i=0;i<spec_commands.length;i++)
    		if(command.trim().split()[0]===spec_commands[i])
    			special_comm_flag=1;
    	//if command is not special then augment it to find its status and time. Otherwise just send it for execution only.
    	if(special_comm_flag!=1)
    	{
	    message=command+"#;echo #"+id+"#:Status=$?time-$((`date '+%s'`))_\r";
    	}
    	else
    	{
	    message=command+"\r";
	    special_comm_flag=0;}
	    iframe.contentWindow.postMessage(message, "*");
    	}
}
button.addEventListener("click", sendMessage);
 
//script to parse messages recieved from iframe.
window.addEventListener('message', function(event) 
{
var x=JSON.parse(event.data);
if(x!=null)
{
	document.getElementById("Time").value=x.time;    
	if(x.status==='0')
		document.getElementById("CES").style.background='green';
	else
		document.getElementById("CES").style.background='red';
}
});
