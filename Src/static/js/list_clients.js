// icons from http://somerandomdude.com/work/iconic/
$(document).ready(function(){
    setClickable();
});
function setClickable() {
    $('#editable').click(function(){
        var revert = $(this).html();
        var substText = ' \
        <div> \
            <input size="40" type="text">' + $(this).html() + '</input> \
            <input type="image" height="32px" \
                        src="/static/images/check_alt.svg" \
                        value="SAVE" class="saveButton" /> \
            <input type="image" height="32px" value="CANCEL" \
                        class="cancelButton" \
                        src="/static/images/x_alt.svg.png"/> \
        </div>';
        $('.saveButton').click(function(){saveChanges(this, false);});
        $('.cancelButton').click(function(){saveChanges(this, revert);});
    });
}


