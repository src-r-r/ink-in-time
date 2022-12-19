function getQuerystring() {
  let output = {};
  if (window.location.search) {
    var queryParams = window.location.search.substring(1);
    var listQueries = queryParams.split("&");
    for (var query in listQueries) {
      if (listQueries.hasOwnProperty(query)) {
        var queryPair = listQueries[query].split("=");
        output[queryPair[0]] = decodeURIComponent(queryPair[1] || "");
      }
    }
  }
  return output;
}

$(document).ready(() => {
  const qs = getQuerystring();
  if (!qs.timezone) {
    // Detect the timezone if not given
    // https://attacomsian.com/blog/javascript-current-timezone
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    console.log(timezone);
    window.location.replace(window.location + `?timezone=${timezone}`);
  }

  $("#timezone-filter").keyup((e) => {
    const searchVal = e.target.value.trim().toLowerCase();
    $(".iit-dropdown li a").each((i, el) => {
      const val = $(el).attr("iit-data-value").trim().toLowerCase();
      if (!searchVal || val.startsWith(searchVal)) {
        $(el).show();
      } else {
        $(el).hide();
      }
    });
  });
});
