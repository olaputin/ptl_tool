/**
 * Created by olaputin on 17/05/16.
 */

function update_task_status(type_operation){
    get_status(type_operation, function(data){
        if(data){
            $('#'+type_operation+'_btn').toggleClass('disabled');
        }
    });
}

function get_status(operation_type, callback){
    $.get('/status/'+operation_type, function(data){
        callback(data);
    });
}

function ptl_request(cmd){
    $.post('/'+cmd, function(data){
        disable_button(cmd);
    })
}

function disable_button(type_operation){
    $('#'+type_operation+'_btn').toggleClass('disabled');
}
