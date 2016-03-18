
var msg;

var socket = new WebSocket("ws://0.0.0.0:8080/ws");
//var socket = new WebSocket("ws://192.168.1.23:8080/ws");

var sendMessage = function(message) {
socket.send(message);
};

socket.onopen = function(){  
console.log("connected"); 
}; 



socket.onmessage = function (message) {
	msg = JSON.parse(message.data);
	for (var key in msg) {
		console.log(' name=' + key);
	    switch (key){

	   		case "ECLightDetector":
	   			updateECText(msg["ECLightDetector"]);

	   		case "log":
	   			console.log("log :"+msg["log"]); 

  		}	

  
	}

};

socket.onclose = function(){
console.log("disconnected"); 
};

var updateECText = function(text) {
	console.log("update ec : "+text);
	$(document).ready(function() {
    	$("p#ECText").text(text+' mS');
	});
	
};



















