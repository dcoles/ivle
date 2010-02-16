$(document).ready(function(){
    $("#new_projectset_form").submit(add_projectset);
    $(".new_project").submit(add_project);
    $('li').show();
    $('.add-project-link').click(show_add);
    $('.add-projectset-link').click(show_add);
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
    add_project_form = $(this);
    function callback(xhr) {
        if (xhr.status == 200) {
            add_project_form.slideToggle('fast');
            var response = JSON.parse(xhr.responseText);
            var projectlist = $('#projectslist_' + response.projectset_id);
            var new_element = response.html.split('\n').slice(1).join('\n');
            projectlist.children(".list_empty_indicator").remove()
            add_section = projectlist.children(".add-project");
            $(add_section).before(new_element).hide().slideDown();
        } else if (xhr.status == 400) {
            alert("Could not create project: " + xhr.getResponseHeader("X-IVLE-Error"));
        } else {
            alert("Project creation failed due to an internal server error.");
        }
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
        var projectset_div = $('#projectset_' + response.projectset_id);
        projectset_div.hide();
        projectset_div.slideDown();
        $("#add_projectset").removeAttr('disabled');
        projectset_div.find(".new_project").submit(add_project);
        projectset_div.find(".add-project-link").click(show_add);
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
