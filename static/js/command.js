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
    json = $.parseJSON(e.data);
    pushCommand.innerHTML = "状态：" + json.pushCommand;

    try{
        ranges = json.task_ranges;
        for (var i=0;i<ranges.length;i++){
            var successed = 0;
            for (var k=0;k<ranges[i].length;k++){
                if (ranges[i][k][2] == 0){
                    $('#range_' + i + '_' + ranges[i][k][0] + '_' + ranges[i][k][1]).removeAttr('class');
                    $('#range_' + i + '_' + ranges[i][k][0] + '_' + ranges[i][k][1]).attr('class', 'btn btn-default');
                }else if (ranges[i][k][2] == 1001){
                    $('#range_' + i + '_' + ranges[i][k][0] + '_' + ranges[i][k][1]).removeAttr('class');
                    $('#range_' + i + '_' + ranges[i][k][0] + '_' + ranges[i][k][1]).attr('class', 'btn btn-warning');
                }else if (ranges[i][k][2] == 1){
                    successed += 1;

                    $('#range_' + i + '_' + ranges[i][k][0] + '_' + ranges[i][k][1]).removeAttr('class');
                    $('#range_' + i + '_' + ranges[i][k][0] + '_' + ranges[i][k][1]).attr('class', 'btn btn-success');
                }
            }
            if (successed == ranges[i].length){
                $('#download_success_' + i).innerHTML = '下载完成';
                $('#download_btn_' + i).attr('value', '删除任务');
                $('#download_btn_' + i).removeAttr('onclick');
				$('#download_btn_' + i).attr('onclick', 'javascript:delete_task(' + i + ')');
            }
        }
    }catch(err){}
}