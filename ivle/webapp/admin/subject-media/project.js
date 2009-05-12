$(document).ready(function(){
    $("#new_projectset_form").submit(add_projectset);
    $(".new_project").submit(add_project);
    $('li').show();
    $('.add-project-link').click(show_add);
});

function serializeForm(form){

    mylist = form.serializeArray();
    var data = {};
    for (var i = 0; i < mylist.length; i++){
        data[mylist[i].name] = mylist[i].value;
    }
    return data;

};

function add_project(){

    $(this.parentNode).slideToggle();
    
    function callback(xhr) {
        var response = JSON.parse(xhr.responseText);
        var projectlist = $('#projectslist_' + response.projectset_id);
        var new_element = response.html.split('\n').slice(1).join('\n');
        projectlist.children(".list_empty_indicator").remove()
        $(new_element).appendTo(projectlist).hide().slideDown();
    };

    var data = serializeForm($(this));

    ajax_call(callback, $(this).attr("action"), "", data, 'POST');

    return false;
};

function add_projectset(){

    $("#add_projectset").attr('disabled', 'disabled');

    function callback(xhr) {
        var response = JSON.parse(xhr.responseText);
        $('#projectset_list').append(response.html);
        $('#projectset_' + response.projectset_id).hide();
        $('#projectset_' + response.projectset_id).slideDown();
        $("#add_projectset").removeAttr('disabled');
        $(".add-project-link").click(show_add);
    };

    var data = serializeForm($("#new_projectset_form"));

    data['ivle.op'] = 'add_projectset';

    ajax_call(callback, $("#new_projectset_form").attr("action"), "", data, 
            'POST');

    return false;
};

function show_add(){
    $(this).next().slideToggle();
    return false;
}
