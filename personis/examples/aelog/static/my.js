$(document).ready(function(){
  $('img.wrapper').click(function(){
  	var t = $(this).attr('alt');
    $.ajax({
         type: 'POST',
         url: 'log_me',
         data: {item: $(this).attr('alt')},
         success: function(data) {
            $('#coll > .ui-collapsible-content ').prepend("<p class='loggedItem'>" +t+' at '+ new Date().toDateString()+'</p>').trigger("create"); 
         }
     });
  });
  
  $('#undo').click(function(){
    var i = $('#coll > .ui-collapsible-content > .loggedItem').first().text();
    i = i.split(' ')[0] + '-';
    console.log(i);
    $.ajax({
         type: 'POST',
         url: 'log_me',
         data: {item: i},
         success: function(data) {
          console.log('Undo was performed. '+data);
          $('#coll > .ui-collapsible-content > .loggedItem').first().remove();
         }
     });
  });
});