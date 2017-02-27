var pushCommand;
var url = '/pushcommand/' //服务端地址
window.onload = function() {
    pushCommand = document.getElementById('pushCommand');
    startListenServer()
}
function startListenServer() {
    var es = new EventSource(url); //连接服务器
    es.onmessage = msg;
}
function msg(e) {
    pushCommand.innerHTML = "状态：" + e.data;  // e.data即服务器返回的数据
}