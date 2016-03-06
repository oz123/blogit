// Empty JS for your own code to be here
$(document).ready(function() {

	$('a.tweet').click(function(e){
	  e.preventDefault();
	  //We get the URL of the link
	  var loc = $(this).attr('href');
	  //We get the title of the link
	  var title  = encodeURIComponent($(this).attr('title'));
	  var title  = escape($(this).attr('title'));
	  //We trigger a new window with the Twitter dialog, in the middle of the page
	  window.open('http://twitter.com/share?url=' + loc + '&text=' + title + '&', 'twitterwindow', 'height=450, width=550, top='+($(window).height()/2 - 225) +', left='+$(window).width()/2 +', toolbar=0, location=0, menubar=0, directories=0, scrollbars=0');
	});

});
