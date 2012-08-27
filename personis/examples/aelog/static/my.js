$(document).ready(function() {
    $('img.wrapper').click(function() {
        var t = $(this);
        $.ajax({
            type: 'POST',
            url: 'log_me',
            data: {
                item: t.attr('alt')
            },
            beforeSend: function(data) {
                t.fadeToggle("fast", "linear");
            },
            success: function(data) {
                $('#coll > .ui-collapsible-content ').prepend("<p class='loggedItem'>" + t.attr('alt') + ' at ' + new Date().toDateString() + '</p>').trigger("create");
                t.fadeToggle("fast", "linear");
            }
        });
    });

    $('#undo').click(function() {
        var i = $('#coll > .ui-collapsible-content > .loggedItem').first().text();
        i = i.split(' ')[0] + '-';
        $.ajax({
            type: 'POST',
            url: 'log_me',
            data: {
                item: i
            },
            success: function(data) {
                $('#coll > .ui-collapsible-content > .loggedItem').first().remove();
            }
        });
    });

});
