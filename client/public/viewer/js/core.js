// ##############################################################################################
// Setup Variables
// ##############################################################################################
var resource_url = ""
// ##############################################################################################
// Global Variables
// ##############################################################################################
// +---------+
// | AG-GRID |
// +---------+
// Global AG-GRID Variables
var gridOptions;
var columnDefs;
var defaultColumnDefs;
var btBringGridBack;
var btDestroyGrid;
// Global Default Column Definitions Variables
var SUMMARY_COLUMNS = ["meteor_timestamp", "meteor_environment", "meteor_region", "meteor_server", "meteor_database", "meteor_query"];
var EXECUTION_COLUMNS = ["meteor_status", "meteor_response", "meteor_execution_time", "meteor_execution_rows", "meteor_output"];
// +--------+
// | IMPORT |
// +--------+
// Global Import File Variable
var IMPORT_FILE;
var DATA;
var COLUMNS;
var INFO;
var ERROR;
// +----------+
// | SETTINGS |
// +----------+
// Global Settings Modal Variables
var SETTINGS_NORMALIZED = {};
var SETTINGS_VISIBLE = {};
var SETTINGS_PINNED = {};
// +--------+
// | FILTER |
// +--------+
// Global Filter Modal Default Dropdown Variables
var FILTER_ENVIRONMENT = []
var FILTER_REGION = [];
var FILTER_SERVER = [];
var FILTER_DATABASE = [];
var FILTER_QUERY = [];
// Global Filter Modal Non Default Dropdown Variables
var FILTER_CUSTOM_COLUMNS = [];
var FILTER_CUSTOM_DATA = {};
// +----------------+
// | TRANSFORMATION |
// +----------------+
// Global Transformation Modal Defult Dropdown Variables
var TRANSFORMATION_QUERY = [];
var TRANSFORMED_DATA = [];
// +--------+
// | ERRORS |
// +--------+
var ERRORS_ENABLED = 0;
// +-------+
// | THEME |
// +-------+
var THEME = 'dark';

// ##############################################################################################
// INIT Methods
// ##############################################################################################

// Init Default Theme
init_theme();

// Load All Components
$(document).ready(() => { init() });

function init() {
  // Disable All Components
  $("#quickFilterInput").attr("disabled", true);
  $("#delete-button").attr("disabled", true);
  $("#info-button").attr("disabled", true);
  $("#settings-button").attr("disabled", true);
  $("#filter-button").attr("disabled", true);
  $("#transformation-button").attr("disabled", true);
  $("#errors-button").attr("disabled", true);
  $("#export-button").attr("disabled", true);

  // Clear Quick Filter
  $("#quickFilterInput").val('');

  // Export Modal - Set Default Dropdown Value
  $("#export-format").val('meteor');
}

function check_uri() {
  var current_url = new URL(window.location.href);
  var uri = current_url.searchParams.get("uri");
  if (uri != null) {
    resource_url = (resource_url[resource_url.length - 1] == '/') ? resource_url : resource_url + '/'
    $("#loading").append("<p>- Retrieving Data URI ...</p>");
    $.getScript(resource_url + uri + '.js')
      .done(function () {
        init_meteor();
      })
      .fail(function () {
        var error_title = "Invalid Uniform Resource Identifier";
        var error_message = "The URI provided is not valid";
        $("#loading").html('');
        show_error(error_title, error_message, '');
      });
  }
}

// ##############################################################################################
// AG-GRID Methods
// ##############################################################################################

function get_column_name(column) {
  var column_name;
  if (column.substring(0, 7) == 'meteor_') column_name = column.substring(7).replace('_', ' ').replace(/\b\w/g, function (l) { return l.toUpperCase() }).replace('Sql', 'SQL').replace('Id', 'ID')
  else column_name = column
  return column_name;
}

function build_columns() {
  var AG_GRID_COLUMNS = [];
  for (var i = 0; i < COLUMNS.length; ++i) {
    var column_name = get_column_name(COLUMNS[i]);
    if (COLUMNS[i] == 'meteor_timestamp') AG_GRID_COLUMNS.push({ headerName: column_name, field: COLUMNS[i], width: 100, sort: 'asc' });
    else if (COLUMNS[i] == 'meteor_status') {
      header_name = 'Execution Status'
      AG_GRID_COLUMNS.push({
        headerName: header_name,
        field: COLUMNS[i],
        width: 50,
        cellClass: function (params) { 
          if (params.value === '0') return 'cell-error';
          else if (params.value === '1') return 'cell-ok';
          else if (params.value === '2') return 'cell-warning';
        }
      });
    }
    else if (COLUMNS[i] == 'meteor_response') {
      header_name = 'Execution Response'
      AG_GRID_COLUMNS.push({
        headerName: header_name,
        field: COLUMNS[i],
        width: 200,
        valueGetter: function meteor_response_ValueGetter(params) {
          var meteor_status = JSON.stringify(params.data.meteor_status);
          if (typeof meteor_status !== 'undefined') {
            meteor_status = (meteor_status == '""') ? '' : meteor_status.replace(/"/g, '');
            if (meteor_status == '1') {
              if (INFO['mode'] == 'deploy' || (INFO['mode'] == 'test' && params.data.meteor_query.toLowerCase().startsWith("select"))) {
                return 'Query successfully executed';
              }
              else if (INFO['mode'] == 'test') return 'Test succeeded';
            }
            else if (meteor_status == '2') return 'A rollback has been executed'
            else return params.data.meteor_response;
          }
          else return params.data.meteor_response;
        }
      });
    }
    else if (COLUMNS[i] == 'meteor_execution_time') {
      header_name = 'Execution Time'
      AG_GRID_COLUMNS.push({
        headerName: header_name,
        field: COLUMNS[i],
        width: 200,
        valueGetter: function execution_time_ValueGetter(params) {
          var execution_time = JSON.stringify(params.data.meteor_execution_time);
          if (typeof execution_time !== 'undefined') {
            execution_time = (execution_time == '""') ? '' : execution_time.slice(-2) == 's"' ? execution_time.replace(/"/g, '') : (execution_time.replace(/"/g, '') + 's');
            return execution_time;
          }
          else return params.data.meteor_execution_time;
        },
        comparator: compare_execution_time
      });
    }
    else if (COLUMNS[i] == 'meteor_output') {
      header_name = 'Execution Output'
      AG_GRID_COLUMNS.push({
        headerName: header_name,
        field: COLUMNS[i],
        width: 200,
        valueGetter: function execution_output_ValueGetter(params) {
          var execution_output = (typeof params.data.meteor_output === 'object') ? JSON.stringify(params.data.meteor_output) : params.data.meteor_output
          if (execution_output == '""') execution_output = '';
          else if (execution_output == '"[]"') execution_output = '[]';
          return execution_output;
        }
      });
    }
    else {
      AG_GRID_COLUMNS.push(
        {
          headerName: column_name,
          field: COLUMNS[i],
          width: 100,
          valueGetter: function (params) {
            var col_name = params.colDef.field;
            var value = params.data[col_name];
            return value;
          },
          comparator: compare_values
        }
      );
    }
  }
  // Assign variables
  columnDefs = AG_GRID_COLUMNS.slice(0);
  defaultColumnDefs = AG_GRID_COLUMNS.slice(0);
}

function build_grid() {
  gridOptions = {
    columnDefs: columnDefs,
    rowSelection: 'multiple',
    animateRows: true,
    onModelUpdated: modelUpdated,
    debug: false,
    defaultColDef: {
      editable: true,
      resizable: true,
      sortable: true,
      filter: true,
      width: 100
    },
    stopEditingWhenGridLosesFocus: true,
    onFirstDataRendered: onFirstDataRendered,
    onSelectionChanged: onSelectionChanged,
    onVirtualColumnsChanged: onVirtualColumnsChanged,
    onDisplayedColumnsChanged: onVirtualColumnsChanged,
    onCellEditingStarted: onCellEditingStarted,
    onCellEditingStopped: onCellEditingStopped,
    onViewportChanged: onViewportChanged,
    onDragStarted: onDragStarted,
    onColumnMoved: onColumnMoved,
    onCellMouseOver: onCellMouseOver,
    onCellMouseOut: onCellMouseOut,
    onCellKeyDown: onCellKeyDown
  };

  gridOptions.getRowClass = function () {
    if (THEME == 'light') return 'light-row';
    else if (THEME == 'dark') return 'dark-row';
  }
}

var rows_hovered = [];

function onCellMouseOver() {
  var components = document.getElementsByClassName('ag-row-hover');
  for (var i = 0; i < components.length; ++i) {
    if (THEME == 'light') components[i].classList.add('light-row-hover');
    else if (THEME == 'dark') components[i].classList.add('dark-row-hover');
    rows_hovered.push(components[i]);
  }
}

function onCellMouseOut() {
  while (rows_hovered.length > 0) {
    if (THEME == 'light') rows_hovered.pop().classList.remove('light-row-hover');
    else if (THEME == 'dark') rows_hovered.pop().classList.remove('dark-row-hover');
  }
}

function onCellKeyDown(e) {
  if (['ArrowUp', 'ArrowDown'].includes(e.event.key)) {
    let cell = gridOptions.api.getFocusedCell()
    let row = gridOptions.api.getDisplayedRowAtIndex(cell.rowIndex)
    let node = gridOptions.api.getRowNode(row.id)
    gridOptions.api.deselectAll()
    node.setSelected(true)
  }
  else if (e.event.key == 'a' && (e.event.ctrlKey || e.event.metaKey)) {
    gridOptions.api.selectAll()
  }
}

function onFirstDataRendered(params) {
  if (THEME == 'dark') apply_dark_theme_scrollbar();

  setTimeout(function () {
    $("#loading").hide('slow', function () {
      $("#bestHtml5Grid").show('slow', function () {
        // Auto Size Grid
        autoSizeAll();

        // Show RowCount & Footer Elements
        $("#rowCount").fadeIn();
        $("#footer").fadeIn();

        // Enable Components
        $("#quickFilterInput").attr("disabled", false);
        $("#delete-button").attr("disabled", false);
        $("#theme-button").attr("disabled", false);
        $("#info-button").attr("disabled", (typeof INFO == 'undefined' || !('total_queries' in INFO)));
        $("#settings-button").attr("disabled", false);
        $("#filter-button").attr("disabled", false);
        $("#transformation-button").attr("disabled", !COLUMNS.includes('meteor_query') || !COLUMNS.includes('meteor_output'));
        $("#errors-button").attr("disabled", !COLUMNS.includes('meteor_database') || !COLUMNS.includes('meteor_query') || !COLUMNS.includes('meteor_status') || !COLUMNS.includes('meteor_response'));
        $("#export-button").attr("disabled", false);

        // Disable Loading on Import Button
        $("#import-button").removeClass("is-loading");

        // Auto Size Grid
        setTimeout(function () {
          autoSizeAll();
        }, 100);
      });
    });
  }, 1000);
}

function load_grid() {
  btBringGridBack = document.querySelector("#btBringGridBack");
  btDestroyGrid = document.querySelector("#btDestroyGrid");

  if (btBringGridBack) {
    btBringGridBack.addEventListener("click", onBtBringGridBack);
    btDestroyGrid.addEventListener("click", onBtDestroyGrid);
  }
  addQuickFilterListener();
  onBtBringGridBack();
};

function onBtBringGridBack() {
  var eGridDiv = document.querySelector("#bestHtml5Grid");
  new agGrid.Grid(eGridDiv, gridOptions);
  if (btBringGridBack) {
    btBringGridBack.disabled = true;
    btDestroyGrid.disabled = false;
  }
  gridOptions.api.setRowData(DATA);
}

function onBtDestroyGrid() {
  btBringGridBack.disabled = false;
  btDestroyGrid.disabled = true;
  gridOptions.api.destroy();
}

function addQuickFilterListener() {
  var eInput = document.querySelector("#quickFilterInput");
  eInput.addEventListener("input", function () {
    var text = eInput.value;
    gridOptions.api.setQuickFilter(text);
    setTimeout(function () {
      // Auto Size Columns
      autoSizeAll();
    }, 100);
  });
}

function modelUpdated() {
  var model = gridOptions.api.getModel();
  var processedRows = model.getRowCount();
  document.querySelector("#rowCount").innerHTML = "<b>" + processedRows.toLocaleString() + "</b> Displayed Rows";
  // Apply Theme
  onVirtualColumnsChanged();
}

function autoSizeAll() {
  var allColumnIds = [];
  gridOptions.columnApi.getAllColumns().forEach(function (column) {
    allColumnIds.push(column.colId);
  });
  gridOptions.columnApi.autoSizeColumns(allColumnIds);
}

function removeSelectedRows() {
  var selectedData = gridOptions.api.getSelectedRows();
  gridOptions.api.updateRowData({ remove: selectedData });
  autoSizeAll();
}

// ##############################################################################################
// IMPORT
// ##############################################################################################
var imported_file_name;

$("#import-button").click(function () {
  // Open File Import Dialog 
  $("#import-file").trigger("click");
});

function updateProgress(evt) {
  // evt is an ProgressEvent.
  if (evt.lengthComputable) {
    var percentLoaded = Math.round((evt.loaded / evt.total) * 100);
    $("#loading").append("<p>- [" + percentLoaded.toString() + " %] Uploading file '" + imported_file_name + "' ...</p>");
  }
}

$("#import-file").change(function (event) {
  $("#import-button").addClass("is-loading");
  $("#loading").html('');

  var error_title = "Invalid File Type";
  var error_message = "Please use a <b>Meteor</b> file format. Example of a <b>meteor.json</b> file:<br><br>";
  var error_code = `{<br>
    &nbsp "DATA": [["row1_col1", "row1_col2"],["row2_col1", "row2_col2"]],<br>
    &nbsp "COLUMNS": ["column1", "column2"]<br>
  }`;
  var file = event.target.files[0];
  if (typeof file == 'undefined') {
    $("#import-button").removeClass("is-loading");
    return;
  }
  var extension = file['name'].substr((file['name'].lastIndexOf('.') + 1));
  if (extension != 'json') show_error(error_title, error_message, error_code);
  else {
    // Re-Init Components
    init()
    // If Grid is Loaded then Destroy it and show the loading page again
    if (typeof gridOptions != 'undefined') {
      $("#bestHtml5Grid").hide();
      $("#rowCount").hide();
      $("#footer").hide();
      $("#loading").show();
      gridOptions.api.destroy();
    }
    $("#theme-button").attr("disabled", true);
    $("#loading").append("<p><b>" + file['name'] + " (" + (file['size'] / 1024 / 1024).toFixed(2) + " MB)</b></p>");
    imported_file_name = file['name'];

    var reader = new FileReader();
    reader.readAsText(file);
    reader.onprogress = updateProgress;
    reader.onload = function (e) {
      try {
        $("#loading").append("<p>- File Uploaded Successfully</p>");
        $("#loading").append("<p>- Processing File ...</p>");
        // Convert String to Executable Javascript Code
        IMPORT_FILE = JSON.parse(e.target.result);
        // Check Errors
        var valid_file = false;
        if (!('DATA' in IMPORT_FILE)) show_error(error_title, error_message, error_code);
        else if (!('COLUMNS' in IMPORT_FILE)) show_error(error_title, error_message, error_code);
        else valid_file = true;
      }
      catch (err) {
        show_error(error_title, error_message, error_code);
      }
      if (valid_file) {
        // Init Meteor Core 
        setTimeout(function () { init_meteor(); }, 100);
      }
    };
  }
});

function init_meteor() {
  // Compile Several Data File Meteor Values.
  $("#loading").append("<p>- Compiling Data ...</p>");
  compile_meteor();
  // Init and Load The AG-GRID
  $("#loading").append("<p>- Building Columns ...</p>");
  build_columns();
  // Init Settings Modal
  $("#loading").append("<p>- Initializing Settings Modal ...</p>");
  init_settings_modal();
  // Init Info Modal
  $("#loading").append("<p>- Initializing Information Modal ...</p>");
  init_info_modal();
  // Init Filter Modal
  $("#loading").append("<p>- Initializing Filter Modal ...</p>");
  init_filter_modal();
  // Init Transformation Modal
  $("#loading").append("<p>- Initializing Transformation Modal ...</p>");
  init_transformation_modal();
  // Convert all Select Dropdown to Select2 Class (+ Apply Theme)
  $("#loading").append("<p>- Stylizing Components ...</p>");
  init_select2()
  // Building Grid
  $("#loading").append("<p>- Assembling Grid ...</p>");
  build_grid();
  // Loading Grid
  $("#loading").append("<p>- Shuffling the Deck ...</p>");
  load_grid();
  $("#loading").append("<p>- Initiating Launch Sequence ...</p>");
}

function compile_meteor() {
  // Compile columns
  COLUMNS = IMPORT_FILE.COLUMNS;
  // Compile data
  DATA = IMPORT_FILE.DATA
  // Compile info
  if ('INFO' in IMPORT_FILE) INFO = IMPORT_FILE.INFO
  // Compile errors
  if ('ERROR' in IMPORT_FILE) ERROR = IMPORT_FILE.ERROR
  // Clean IMPORT_FILE
  IMPORT_FILE = null
  // Get the Custom Columns
  for (var i = 0; i < COLUMNS.length; ++i) {
    if (!SUMMARY_COLUMNS.includes(COLUMNS[i]) && !EXECUTION_COLUMNS.includes(COLUMNS[i])) FILTER_CUSTOM_COLUMNS.push(COLUMNS[i]);
  }
}

function init_select2() {
  $('.js-example-basic-single').select2();
  if (THEME == 'light') apply_light_theme_select2();
  else apply_dark_theme();
}

function normalize(str) {
  let string = ''
  // Remove accents & lowercase (adding a letter to the beginning)
  str = 'a' + str.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
  // Replace non standard values to '_'
  for (let i = 0; i < str.length; ++i) {
    if (/[a-zA-Z]/.test(str[i]) === false && !(['0','1','2','3','4','5','6','7','8','9','-','_','.'].includes(str[i]))) string += '_'
    else string += str[i]
  }
  // Ensure the string endswith a letter
  string += 'a'
  return string
}

// ##############################################################################################
// DELETE ROWS
// ##############################################################################################
$("#delete-button").click(function () {
  $("#delete-button").addClass("is-loading");
  setTimeout(function () {
    removeSelectedRows();
    $("#delete-button").removeClass("is-loading");
  }, 100);
});

// ##############################################################################################
// SETTINGS MODAL
// ##############################################################################################

$("#settings-button").click(function () {
  enable_settings_modal(true);
  $("#settings-modal").addClass("is-active");
});

$("#settings-modal-close").click(function () {
  enable_settings_modal(false);
  close_settings_modal();
});

$("#settings-modal-cancel").click(function () {
  enable_settings_modal(false);
  close_settings_modal();
});

$("#settings-modal-save").click(function () {
  // Add Button Loading Effect
  $("#settings-modal-save").addClass("is-loading");

  // Disable All Modal Objects
  enable_settings_modal(false);

  setTimeout(function () {
    // Recompile data
    apply_settings_modal();
    // Remove Button Loading Effect
    $("#settings-modal-save").removeClass("is-loading");
    // Hide Settings Modal
    close_settings_modal();
  }, 10);
});

function init_settings_modal() {
  for (var i = 0; i < COLUMNS.length; ++i) {
    SETTINGS_NORMALIZED[this.normalize(COLUMNS[i])] = COLUMNS[i];
    var column_name = get_column_name(COLUMNS[i]);
    // Pinned Columns
    $("#settings-modal-visible_fields").append("<div class='pretty p-svg p-plain' style='top:2px; margin-right:10px'><input id='" + this.normalize(COLUMNS[i]) + "_pinned' type='checkbox' checked/><svg id='" + this.normalize(COLUMNS[i]) + "_pinned_svg' class='svg' viewBox='0 0 8 8' style='fill: #00c4a7; position: relative; width:16px'><use xlink:href='css/open-iconic.svg#lock-unlocked'></use></svg><label></label></div>");
    $("#" + this.normalize(COLUMNS[i]) + "_pinned").click(function () {
      // Change the image
      var inner_html = $("#" + $(this)[0]['id'] + "_svg").html();
      if (inner_html == '<use xlink:href="css/open-iconic.svg#lock-unlocked"></use>') {
        $("#" + $(this)[0]['id'] + "_svg").css('fill', '#ff6961');
        $("#" + $(this)[0]['id'] + "_svg").css('top', '2px');
        $("#" + $(this)[0]['id'] + "_svg").html('<use xlink:href="css/open-iconic.svg#lock-locked"></use>');
      }
      else {
        $("#" + $(this)[0]['id'] + "_svg").css('fill', '#00c4a7');
        $("#" + $(this)[0]['id'] + "_svg").css('top', '0px');
        $("#" + $(this)[0]['id'] + "_svg").html('<use xlink:href="css/open-iconic.svg#lock-unlocked"></use>');
      }
      $("#" + $(this)[0]['id']).prop('checked', true);
      // Change the value
      var id = $(this)[0]['id'].substring(0, $(this)[0]['id'].length - 7);
      SETTINGS_PINNED[id] = !SETTINGS_PINNED[id];
    });
    SETTINGS_PINNED[this.normalize(COLUMNS[i])] = false;
    // Visible Columns
    $("#settings-modal-visible_fields").append("<div class='pretty p-svg p-curve' style='margin-bottom:10px;'><img id='" + this.normalize(COLUMNS[i]) + "_visible' src='res/visible.svg' width=20 height=20 style='margin-top:-2px; cursor:pointer;'><label style='margin-left:12px;'>" + column_name + "</label></div><br>");
    $("#" + this.normalize(COLUMNS[i]) + "_visible").click(function () {
      // Change the image
      var img_src = $("#" + $(this)[0]['id']).attr("src");
      if (img_src == 'res/visible.svg') $("#" + $(this)[0]['id']).attr("src", "res/hidden.svg");
      else $("#" + $(this)[0]['id']).attr("src", "res/visible.svg");
      // Change the value
      var id = $(this)[0]['id'].substring(0, $(this)[0]['id'].length - 8);
      SETTINGS_VISIBLE[id] = !SETTINGS_VISIBLE[id];
    });
    SETTINGS_VISIBLE[this.normalize(COLUMNS[i])] = true;
  }
}

function set_column_pinned(column_name, is_pinned) {
  if (is_pinned) {
    $("#" + this.normalize(column_name) + "_pinned_svg").css('fill', '#ff6961');
    $("#" + this.normalize(column_name) + "_pinned_svg").css('margin-top', '2px');
    $("#" + this.normalize(column_name) + "_pinned_svg").html('<use xlink:href="css/open-iconic.svg#lock-locked"></use>');
  }
  else {
    $("#" + this.normalize(column_name) + "_pinned_svg").css('fill', '#00c4a7');
    $("#" + this.normalize(column_name) + "_pinned_svg").css('margin-top', '0px');
    $("#" + this.normalize(column_name) + "_pinned_svg").html('<use xlink:href="css/open-iconic.svg#lock-unlocked"></use>');
  }
  SETTINGS_PINNED[column_name] = is_pinned;
}

function set_column_visible(column_name, is_visible) {
  if (is_visible) $("#" + this.normalize(column_name) + "_visible").attr("src", "res/visible.svg");
  else $("#" + this.normalize(column_name) + "_visible").attr("src", "res/hidden.svg");
  SETTINGS_VISIBLE[column_name] = is_visible
}

function apply_settings_modal() {
  // Pinned Columns
  var pinned = Object.keys(SETTINGS_PINNED).sort();
  for (var i = 0; i < pinned.length; i++) {
    var pinned_value = (SETTINGS_PINNED[pinned[i]]) ? 'left' : null;
    gridOptions.columnApi.setColumnPinned(SETTINGS_NORMALIZED[pinned[i]], pinned_value);
  }
  // Visible Columns
  var visible = Object.keys(SETTINGS_VISIBLE).sort();
  for (var i = 0; i < visible.length; i++) {
    gridOptions.columnApi.setColumnVisible(SETTINGS_NORMALIZED[visible[i]], SETTINGS_VISIBLE[visible[i]]);
  }
  setTimeout(function () {
    // Auto Size Columns
    autoSizeAll();
  }, 100);
}

function close_settings_modal() {
  $("#settings-modal").removeClass('fadeIn');
  $("#settings-modal").addClass('fadeOut');
  setTimeout(function () {
    $("#settings-modal").removeClass("is-active");
    $("#settings-modal").removeClass('fadeOut');
    $("#settings-modal").addClass('fadeIn');
  }, 300);
}

function enable_settings_modal(option) {
  // Enable/Disable All Settings Modal Objects
  $("#settings-modal-cancel").attr('disabled', !option);
  $("#settings-modal-close").attr('disabled', !option);
  $("#settings-modal-save").attr('disabled', !option);
}

// ##############################################################################################
// INFORMATION MODAL
// ##############################################################################################

$("#info-button").click(function () {
  $("#info-modal").addClass("is-active");
});

$("#info-modal-close").click(function () {
  close_info_modal();
});

$("#info-modal-save").click(function () {
  close_info_modal();
});

function close_info_modal() {
  $("#info-modal").removeClass('fadeIn');
  $("#info-modal").addClass('fadeOut');
  setTimeout(function () {
    $("#info-modal").removeClass("is-active");
    $("#info-modal").removeClass('fadeOut');
    $("#info-modal").addClass('fadeIn');
  }, 300);
}

function init_info_modal() {
  if (typeof INFO == 'undefined' || !('total_queries' in INFO)) return;
  // +------+
  // | TEST |
  // +------+
  if (INFO['mode'] == 'test') {
    // Queries Tested
    $("#info-modal-fields").prepend('<span id="info-queries" class="tag is-info" style="font-size:1.1rem; font-weight:500; width:100%;">Total Queries: <b style="margin-left:5px;">' + INFO['total_queries'] + '</b></span>');
    $("#info-execution-title").text('TEST EXECUTION');
    // Queries Passed the Test Execution
    var info_execution_checks_successful_value = INFO['total_queries'] - INFO['queries_failed'];
    var info_execution_checks_successful_percentage = 0.0;
    if (INFO['total_queries'] != 0) {
      info_execution_checks_successful_percentage = (Number.parseFloat(INFO['total_queries'] - INFO['queries_failed']) / Number.parseFloat(INFO['total_queries']) * 100).toFixed(2);
    }
    $("#info-modal-fields").append('<div style="margin-top:10px;"><span id="info-execution-checks-successful" class="tag is-success" style="font-size:1.1rem; font-weight:500; margin-bottom: 0.25rem; width:100%; background-color:#00c4a7;">Queries Succeeded: <b style="margin-left:5px;">' + info_execution_checks_successful_value + '</b><span style="font-weight:400; margin-left:5px;">(~' + info_execution_checks_successful_percentage + '%)</span></span></div>');

    // Queries Failed the Test Execution
    var execution_checks_failed_value = INFO['queries_failed'];
    var execution_checks_failed_percentage = 0.0;
    if (INFO['total_queries'] != 0) {
      execution_checks_failed_percentage = (Number.parseFloat(INFO['queries_failed']) / Number.parseFloat(INFO['total_queries']) * 100).toFixed(2);
    }
    $("#info-modal-fields").append('<div><span id="info-execution-checks-failed" class="tag" style="font-size:1.1rem; font-weight:500; width:100%; background-color:#ff6961;">Queries Failed: <b style="margin-left:5px;">' + execution_checks_failed_value + '</b><span style="font-weight:400; margin-left:5px;">(~' + execution_checks_failed_percentage + '%)</span></span></div>');
    if (INFO['queries_failed'] == 0) $("#info-execution-checks-failed").addClass("is-success");
    else $("#info-execution-checks-failed").addClass("is-danger");
  }

  // +--------+
  // | DEPLOY |
  // +--------+
  else if (INFO['mode'] == 'deploy') {
    // Queries Executed
    $("#info-modal-fields").prepend('<span id="info-queries" class="tag is-info" style="font-size:1.1rem; font-weight:500; width:100%;">Queries Executed: <b style="margin-left:5px;">' + INFO['total_queries'] + '</b></span>');
    $("#info-execution-title").text('DEPLOYMENT');
    // Queries Succeeded
    var info_queries_succeeded_value = INFO['total_queries'] - INFO['queries_failed'];
    var info_queries_succeeded_percentage = 0.0;
    if (INFO['total_queries'] != 0) {
      info_queries_succeeded_percentage = (Number.parseFloat(Number.parseInt(INFO['total_queries']) - Number.parseInt(INFO['queries_failed'])) / Number.parseFloat(INFO['total_queries']) * 100).toFixed(2);
    }
    $("#info-modal-fields").append('<div style="margin-top:10px;"><span id="info-queries-succeeded" class="tag" style="font-size:1.1rem; font-weight:500; margin-bottom: 0.25rem; width:100%; background-color:#00c4a7; color:#fff;">Queries Succeeded: <b style="margin-left:5px;">' + info_queries_succeeded_value + '</b><span style="font-weight:400; margin-left:5px;">(~' + info_queries_succeeded_percentage + '%)</span></span></div>');

    // Queries Failed
    var info_queries_failed_value = INFO['queries_failed'];
    var queries_failed_percentage = 0.0;
    if (INFO['total_queries'] != 0) {
      queries_failed_percentage = (Number.parseFloat(INFO['queries_failed']) / Number.parseFloat(INFO['total_queries']) * 100).toFixed(2);
    }
    $("#info-modal-fields").append('<div><span id="info-queries-failed" class="tag" style="font-size:1.1rem; font-weight:500; margin-bottom: 0.25rem; width:100%; background-color:#ff6961; color:#fff;">Queries Failed: <b style="margin-left:5px;">' + info_queries_failed_value + '</b> <span style="font-weight:400; margin-left:5px;">(~' + queries_failed_percentage + '%)</span></span></div>');
  }

  // +--------+
  // | ERRORS |
  // +--------+
  if (typeof ERROR == 'undefined') {
    var test_execution = ('queries_failed' in INFO) ? 'Test ' : ''
    if (('queries_failed' in INFO && INFO['queries_failed'] > 0) || ('queries_failed' in INFO && INFO['queries_failed'] > 0)) {
      $("#info-modal-fields").append('<h3 class="is-info" style="margin-top: 1.0rem; text-size:0.9rem;">' + test_execution + 'Execution Finished With Errors</h3>');
    }
    else {
      $("#info-modal-fields").append('<h3 class="is-info" style="margin-top: 1.0rem; text-size:0.9rem;">' + test_execution + 'Execution Finished Successfully</h3>');
    }
  }
  else if (ERROR == '') {
    // Execution Interrupted
    $("#info-modal-fields").append('<h3 class="is-info" style="margin-top: 1.0rem; margin-bottom: 1.0rem;">Execution Interrupted</h3>');
  }
  else {
    // Execution Failed
    $("#info-modal-fields").append('<h3 class="is-info" style="margin-top: 1.0rem; margin-bottom: 1.0rem;">Execution Failed. An error occurred.</h3>');
    $("#info-modal-fields").append('<h3 class="tag is-danger" style="background-color:#ef5353; padding-top:5px; padding-bottom: 5px; height: auto; font-size:0.95rem; white-space: pre-wrap; width:100%">' + ERROR + '</h3>');
  }
}

// ##############################################################################################
// FILTER MODAL
// ##############################################################################################
var filter_environment_selected = filter_region_selected = filter_server_selected = filter_database_selected = filter_query_selected = 0;
var data = []

$("#filter-button").click(function () {
  // Add Loading Class to Button
  $("#filter-button").addClass("is-loading");

  setTimeout(function () {
    // Enable All Modal Objects
    enable_filter_modal(true);

    // Set Dropdown Values
    $("#filter-environment").val(filter_environment_selected).trigger('change');
    $("#filter-region").val(filter_region_selected).trigger('change');
    $("#filter-server").val(filter_server_selected).trigger('change');
    $("#filter-database").val(filter_database_selected).trigger('change');
    $("#filter-query").val(filter_query_selected).trigger('change');
    // Show Filter Modal
    $("#filter-modal").addClass("is-active");
    // Remove Loading Class to Button
    $("#filter-button").removeClass("is-loading");
  }, 100);
});

$("#filter-modal-close").click(function () {
  enable_filter_modal(false);
  close_filter_modal();
});

$("#filter-modal-cancel").click(function () {
  enable_filter_modal(false);
  close_filter_modal();
});

$("#filter-modal-save").click(function () {
  // Disable All Modal Objects
  enable_filter_modal(false);
  // Add Button Loading Effect
  $("#filter-modal-save").addClass("is-loading");

  setTimeout(function () {
    // Store Dropdown Values
    filter_environment_selected = $('#filter-environment').val();
    filter_region_selected = $('#filter-region').val();
    filter_server_selected = $('#filter-server').val();
    filter_database_selected = $('#filter-database').val();
    filter_query_selected = $('#filter-query').val();
    // Apply Filter
    filter_data();
    // Remove Button Loading Effect
    $("#filter-modal-save").removeClass("is-loading");
    // Hide Filter Modal
    close_filter_modal();
  }, 100);
});

function init_filter_modal() {
  // Init Variables
  FILTER_ENVIRONMENT = []
  FILTER_REGION = []
  FILTER_SERVER = []
  FILTER_DATABASE = []
  FILTER_QUERY = []

  // Init UI Elements
  elements = ['meteor_environment', 'meteor_region', 'meteor_server', 'meteor_database', 'meteor_query'];
  for (var i = 0; i < elements.length; ++i) {
    if (!COLUMNS.includes(elements[i])) {
      $("#filter-modal-" + elements[i] + "-div").fadeOut();
    }
  }
  // Get Dropdown Values
  for (let i = 0; i < DATA.length; ++i) {
    if ('meteor_environment' in DATA[i] && !FILTER_ENVIRONMENT.includes(DATA[i]['meteor_environment'])) FILTER_ENVIRONMENT.push(DATA[i]['meteor_environment']);
    if ('meteor_region' in DATA[i] && !FILTER_REGION.includes(DATA[i]['meteor_region'])) FILTER_REGION.push(DATA[i]['meteor_region']);
    if ('meteor_server' in DATA[i] && !FILTER_SERVER.includes(DATA[i]['meteor_server'])) FILTER_SERVER.push(DATA[i]['meteor_server']);
    if ('meteor_database' in DATA[i] && !FILTER_DATABASE.includes(DATA[i]['meteor_database'])) FILTER_DATABASE.push(DATA[i]['meteor_database']);
    if ('meteor_query' in DATA[i] && FILTER_QUERY.length < 10000 && !FILTER_QUERY.includes(DATA[i]['meteor_query'])) {
      if (DATA[i]['meteor_query'].startsWith('[')) {
        // Parse Query Alias
        let stack = 0
        for (let j = 1; j < DATA[i]['meteor_query'].length; ++j) {
          if (DATA[i]['meteor_query'][j] == '[') stack += 1
          else if (DATA[i]['meteor_query'][j] == ']') {
            if (stack == 0) {
              let element = '[ALIAS] ' + DATA[i]['meteor_query'].substr(1, j - 1)
              if (!FILTER_QUERY.includes(element)) FILTER_QUERY.push(element)
              break
            }
            else stack -= 1
          }
        }
      }
      else FILTER_QUERY.push(DATA[i]['meteor_query']);
    }
  }

  // Show warning message
  if (FILTER_QUERY.length == 10000) $('#filter-modal-meteor_query-limit-div').css({ display : "inline" });
  else $('#filter-modal-meteor_query-limit-div').css({ display : "none" });

  // Sort Dropdown Values
  FILTER_ENVIRONMENT.sort();
  FILTER_REGION.sort();
  FILTER_SERVER.sort();
  FILTER_DATABASE.sort();
  FILTER_QUERY.sort();
  // Init Dropdown Values
  for (var i = 0; i < FILTER_ENVIRONMENT.length; ++i) $('#filter-environment').append($('<option>', { value: i + 1, text: FILTER_ENVIRONMENT[i] }))
  for (var i = 0; i < FILTER_REGION.length; ++i) $('#filter-region').append($('<option>', { value: i + 1, text: FILTER_REGION[i] }))
  for (var i = 0; i < FILTER_SERVER.length; ++i) $('#filter-server').append($('<option>', { value: i + 1, text: FILTER_SERVER[i] }))
  for (var i = 0; i < FILTER_DATABASE.length; ++i) $('#filter-database').append($('<option>', { value: i + 1, text: FILTER_DATABASE[i] }))
  for (var i = 0; i < FILTER_QUERY.length; ++i) $('#filter-query').append($('<option>', { value: i + 1, text: FILTER_QUERY[i] }))

  /////////////////////
  // CUSTOM ELEMENTS //
  /////////////////////

  // Add Non Default Column Elements
  for (var i = 0; i < FILTER_CUSTOM_COLUMNS.length; ++i) FILTER_CUSTOM_DATA[FILTER_CUSTOM_COLUMNS[i]] = [];
  for (var i = 0; i < DATA.length; ++i) {
    for (var j = 0; j < FILTER_CUSTOM_COLUMNS.length; ++j) {
      if (!FILTER_CUSTOM_DATA[FILTER_CUSTOM_COLUMNS[j]].includes(DATA[i][FILTER_CUSTOM_COLUMNS[j]])) FILTER_CUSTOM_DATA[FILTER_CUSTOM_COLUMNS[j]].push(DATA[i][FILTER_CUSTOM_COLUMNS[j]]);
    }
  }
  // Sort Non Default Column Elements
  for (var i = 0; i < FILTER_CUSTOM_COLUMNS.length; ++i) FILTER_CUSTOM_DATA[FILTER_CUSTOM_COLUMNS[i]].sort();
  // Create Dropdown Elements
  for (var i = 0; i < FILTER_CUSTOM_COLUMNS.length; ++i) {
    var column_name = get_column_name(FILTER_CUSTOM_COLUMNS[i]);
    $('#filter-modal-content').append(`
      <div id="filter-modal-` + this.normalize(FILTER_CUSTOM_COLUMNS[i]) + `-div" style="width:100%; margin-top:10px;">
        <!-- ` + column_name + ` -->
        <div style="width:20%; float:left; margin-top:2px; text-align:right; padding-right: 10px;">
          <span>` + column_name + `:</span>
        </div>
        <div style="width:80%; float:left;">
          <select id="filter-` + this.normalize(FILTER_CUSTOM_COLUMNS[i]) + `" class="js-example-basic-single" name="state" style="width:50%;">
            <option value="0">- All Data -</option>
          </select>
        </div>
      </div>`);
  }
  // Init Dropdown Values
  for (var i = 0; i < FILTER_CUSTOM_COLUMNS.length; ++i) {
    for (var j = 0; j < FILTER_CUSTOM_DATA[FILTER_CUSTOM_COLUMNS[i]].length; ++j) {
      $('#filter-' + this.normalize(FILTER_CUSTOM_COLUMNS[i])).append($('<option>', { value: i + 1, text: FILTER_CUSTOM_DATA[FILTER_CUSTOM_COLUMNS[i]][j] }))
    }
  }
}

function filter_data() {
  // Usable Variables
  var api = gridOptions.api;
  var data = [];

  // Get Dropdown Selected Text Values
  var environment_text = $("#filter-environment option:selected").text();
  var region_text = $("#filter-region option:selected").text();
  var server_text = $("#filter-server option:selected").text();
  var database_text = $("#filter-database option:selected").text();
  var query_text = $("#filter-query option:selected").text();
  var is_alias = query_text.startsWith('[ALIAS] ')

  // Clear All Cells
  api.setRowData([]);

  // Check if Apply Filter on Raw Data or Transformed Data
  var data2filter = [];
  if (transformation_query_selected == 0) {
    // Reset Grid Columns
    for (var i = 0; i < columnDefs.length; ++i) {
      if (columnDefs[i]['field'] == 'meteor_database') columnDefs[i]['pinned'] = null;
    }
    gridOptions.api.setColumnDefs(defaultColumnDefs);
    // Apply Column Properties to Settings Modal
    apply_settings_modal();

    // Set data2filter to all Raw Data 
    data2filter = DATA.slice(0);
  }
  else data2filter = TRANSFORMED_DATA.slice(0);

  // Check the Matching Rows to be Rebuild
  for (var i = 0; i < data2filter.length; ++i) {
    var row_match = true;
    // Default Elements
    var environment_condition = (filter_environment_selected == 0) ? 1 : ((data2filter[i]['meteor_environment'] == environment_text) ? 1 : 0)
    let region_condition = (filter_region_selected == 0) ? 1 : ((data2filter[i]['meteor_region'] == region_text) ? 1 : 0)
    let server_condition = (filter_server_selected == 0) ? 1 : ((data2filter[i]['meteor_server'] == server_text) ? 1 : 0)
    let database_condition = (filter_database_selected == 0) ? 1 : ((data2filter[i]['meteor_database'] == database_text) ? 1 : 0)
    let query_condition = (filter_query_selected == 0) ? 1 : (!is_alias && data2filter[i]['meteor_query'] == query_text) || (is_alias && data2filter[i]['meteor_query'].startsWith('[' + query_text.substr(8, query_text.length) + ']')) ? 1 : 0
    row_match = (environment_condition & region_condition & server_condition & database_condition & query_condition);
    // Custom Elements
    for (var j = 0; j < FILTER_CUSTOM_COLUMNS.length; ++j) {
      var row_selected = $("#filter-" + this.normalize(FILTER_CUSTOM_COLUMNS[j])).val();
      var row_value = $("#filter-" + this.normalize(FILTER_CUSTOM_COLUMNS[j]) + " option:selected").text();
      row_match &= (row_selected == 0) ? 1 : ((data2filter[i][FILTER_CUSTOM_COLUMNS[j]] == row_value) ? 1 : 0)
    }
    // If Row Match the Filter, then show the row
    if (row_match) data.push(data2filter[i]);
  }
  // Add Matching Rows
  api.updateRowData({ add: data });
  // Resize All Columns
  setTimeout(function () {
    // Auto Size Columns
    autoSizeAll();
  }, 100);
}

function close_filter_modal() {
  $("#filter-modal").removeClass('fadeIn');
  $("#filter-modal").addClass('fadeOut');
  setTimeout(function () {
    $("#filter-modal").removeClass("is-active");
    $("#filter-modal").removeClass('fadeOut');
    $("#filter-modal").addClass('fadeIn');
  }, 300);
}

function enable_filter_modal(option) {
  // Enable/Disable All Filter Modal Objects
  $('#filter-environment').attr("disabled", !option);
  $('#filter-region').attr("disabled", !option);
  $('#filter-server').attr("disabled", !option);
  $('#filter-database').attr("disabled", !option);
  $('#filter-query').attr("disabled", !option);
  $("#filter-modal-cancel").attr('disabled', !option);
  $("#filter-modal-close").attr('disabled', !option);
  $("#filter-modal-save").attr('disabled', !option);
}

// ##############################################################################################
// TRANSFORMATION MODAL
// ##############################################################################################
var transformation_query_selected = 0;
var transformation_checkbox_checked = false;

$("#transformation-button").click(function () {
  // Add Loading Class to Button
  $("#transformation-button").addClass("is-loading");

  setTimeout(function () {
    // Enable All Modal Objects
    enable_transformation_modal(true);
    // Set Dropdown Values
    $("#transformation-query").val(transformation_query_selected).trigger('change');
    // Set Checkbox Value
    $("#transformation_checkbox").prop("checked", transformation_checkbox_checked);
    $("#transformation_checkbox").attr("disabled", $("#transformation-query").val() == 0);
    // Show Transformation Modal
    $("#transformation-modal").addClass("is-active");
    // Remove Loading Class to Button
    $("#transformation-button").removeClass("is-loading");
  }, 100);
});

$("#transformation-query").on('select2:select', function (e) {
  if (e.params.data.id == 0) $("#transformation_checkbox").prop("checked", false);
  $("#transformation_checkbox").attr("disabled", e.params.data.id == 0);
});

$("#transformation_checkbox_text").click(function () {
  if ($("#transformation-query").val() != 0) $("#transformation_checkbox").prop("checked", !$("#transformation_checkbox").is(":checked"));
});

$("#transformation-modal-close").click(function () {
  enable_transformation_modal(false);
  close_transformation_modal();
});

$("#transformation-modal-cancel").click(function () {
  enable_transformation_modal(false);
  close_transformation_modal();
});

$("#transformation-modal-save").click(function () {
  // Disable All Modal Objects
  enable_transformation_modal(false);
  // Add Button Loading Effect
  $("#transformation-modal-save").addClass("is-loading");

  setTimeout(function () {
    // Store Dropdown Values
    transformation_query_selected = $('#transformation-query').val();
    // Store Checkbox Value
    transformation_checkbox_checked = $("#transformation_checkbox").is(":checked");
    // Apply Filter
    transform_data();
    // Remove Button Loading Effect
    $("#transformation-modal-save").removeClass("is-loading");
    // Hide Transformation Modal
    close_transformation_modal();
  }, 100);
});

function close_transformation_modal() {
  $("#transformation-modal").removeClass('fadeIn');
  $("#transformation-modal").addClass('fadeOut');
  setTimeout(function () {
    $("#transformation-modal").removeClass("is-active");
    $("#transformation-modal").removeClass('fadeOut');
    $("#transformation-modal").addClass('fadeIn');
  }, 300);
}

function enable_transformation_modal(option) {
  // Enable/Disable All Transformation Modal Objects
  $('#transformation-query').attr("disabled", !option);
  $("#transformation-modal-cancel").attr('disabled', !option);
  $("#transformation-modal-close").attr('disabled', !option);
  $("#transformation-modal-save").attr('disabled', !option);
}

function init_transformation_modal() {
  // Init Variables
  TRANSFORMATION_QUERY = []

  // Do not init if there's no query in DATA
  if (!COLUMNS.includes('meteor_query') || !COLUMNS.includes('meteor_output')) return

  // Init UI Elements
  elements = ['meteor_query'];
  for (var i = 0; i < elements.length; ++i) {
    if (!COLUMNS.includes(elements[i])) {
      $("#transformation-modal-" + this.normalize(elements[i]) + "-div").fadeOut();
    }
  }
  // Get Dropdown Values
  for (let i = 0; i < DATA.length; ++i) {
    if (TRANSFORMATION_QUERY.length == 10000) break
    if (!TRANSFORMATION_QUERY.includes(DATA[i]['meteor_query'])) {
      if (DATA[i]['meteor_query'].startsWith('[')) {
        // Parse Query Alias
        let stack = 0
        for (let j = 1; j < DATA[i]['meteor_query'].length; ++j) {
          if (DATA[i]['meteor_query'][j] == '[') stack += 1
          else if (DATA[i]['meteor_query'][j] == ']') {
            if (stack == 0) {
              let element = '[ALIAS] ' + DATA[i]['meteor_query'].substr(1, j - 1)
              if (!TRANSFORMATION_QUERY.includes(element)) TRANSFORMATION_QUERY.push(element)
              break
            }
            else stack -= 1
          }
        }
      }
      else TRANSFORMATION_QUERY.push(DATA[i]['meteor_query'])
    }
  }

  // Show warning message
  if (TRANSFORMATION_QUERY.length == 10000) $('#transformation-query-limit').css({ display : "inline" });
  else $('#transformation-query-limit').css({ display : "none" });

  // Sort Dropdown Values
  TRANSFORMATION_QUERY.sort()
  // Init Dropdown Values
  $('#transformation-query').empty()
  $('#transformation-query').append($('<option>', { value: 0, text: '- No Transformation -' }))
  for (let i = 0; i < TRANSFORMATION_QUERY.length; ++i) {
    $('#transformation-query').append($('<option>', { value: i + 1, text: TRANSFORMATION_QUERY[i] }))
  }
}

function transform_data() {
  // Usable Variables
  var api = gridOptions.api;
  var data = [];

  if (transformation_query_selected != 0) {
    // Disable Error Tab Button
    $("#errors-button").attr("disabled", true);
    // Recompile Query
    data = compile_query(DATA);
    // Store Transformed Data
    TRANSFORMED_DATA = data.slice(0)
    // Set Database Column Visible
    if (COLUMNS.includes('meteor_database') && data.length > 0) set_column_visible('meteor_database', true);
    // Add Matching Rows
    api.setRowData(data);
  }
  else {
    // Enable Error Tab Button
    $("#errors-button").attr("disabled", false);
    // Get Origin Data
    data = DATA.slice(0);
    // Clear Transformed Data
    TRANSFORMED_DATA = [];
    // Set Origin Columns
    var columnDefs = gridOptions.columnDefs.slice(0);
    api.setColumnDefs(columnDefs);
    // Set All Columns Visible
    for (var i = 0; i < COLUMNS.length; ++i) set_column_visible(COLUMNS[i], true);
    // Unpin Database Column
    set_column_pinned('meteor_database', false);
  }
  // Apply Matching Columns
  apply_settings_modal();
  // Apply Current Filter
  filter_data();
  // Resize All Columns
  setTimeout(function () {
    // Auto Size Columns
    autoSizeAll();
  }, 100);
}

function compile_query(data) {
  var api = gridOptions.api;
  var columns = [];
  var new_data = [];

  // Get Dropdown Selected Text Values
  var transformation_query = $("#transformation-query option:selected").text();
  var is_alias = transformation_query.startsWith('[ALIAS] ')

  // Rebuild Data + Rebuild Columns
  for (var i = 0; i < data.length; ++i) {
    if (typeof data[i]['meteor_output'] == 'undefined' || typeof data[i]['meteor_output'] == 'number' || data[i]['meteor_output'].length == 0) continue;
    if (!is_alias && data[i]['meteor_query'] != transformation_query) continue;
    if (is_alias && !data[i]['meteor_query'].startsWith('[' + transformation_query.substr(8, transformation_query.length) + ']')) continue;
    // Rebuild Columns
    if (data[i]['meteor_output'] != '[]') {
      var keys = Object.keys(data[i]['meteor_output'][0]).toString().split(',');
      for (var k = 0; k < keys.length; ++k) {
        if (columns.indexOf(keys[k]) == -1) columns.push(keys[k]);
      }
    }
    // Rebuild Data
    if (data[i]['meteor_output'] == '[]') {
      if (!transformation_checkbox_checked) {
        let expand = columns.reduce((acc, val) => {
          acc[val] = ''
          return acc
        },{})
        new_data.push({...data[i], meteor_output:[], ...expand});
      }
    }
    else if (data[i]['meteor_output'] != '') {
      for (let j = 0; j < data[i]['meteor_output'].length; ++j) {
        let has_values = Object.values(data[i]['meteor_output'][j]).some(x => x != null && x.toString().trim().length > 0)
        if (!transformation_checkbox_checked || has_values) {
          let expand = columns.reduce((acc, val) => {
            acc[val] = data[i]['meteor_output'][j][val]
            return acc
          },{})
          new_data.push({...data[i], meteor_output:[], ...expand});
        }
      }
    }
  }

  // Rebuild New Columns
  var columnDefs = gridOptions.columnDefs.slice(0);
  for (var i = 0; i < columns.length; ++i) {
    columnDefs.push(
      {
        headerName: columns[i],
        field: columns[i],
        valueGetter: function (params) {
          var col_name = params.colDef.field;
          var value = params.data[col_name];
          return value;
        },
        comparator: compare_values
      });
  }

  // Hide Default Columns
  for (var i = 0; i < COLUMNS.length; ++i) set_column_visible(COLUMNS[i], false);

  // Show & Pin Database Column
  if (COLUMNS.includes('meteor_database') && data.length > 0) {
    set_column_visible('meteor_database', true);
    set_column_pinned('meteor_database', true);
  }

  // Set New Columns
  api.setColumnDefs(columnDefs);

  // Return new Grid Data
  return new_data;
}

function compare_values(value1, value2) {
  // Normalize values
  if (value1 == undefined) value1 = null
  if (value2 == undefined) value2 = null
  // Check NULL & Empty Values
  if ((value1 === null && value2 === null) || (value1 !== null && value2 !== null && value1.toString().trim() == '' && value2.toString().trim() == '')) return 0;
  if ((value1 === null) || (value1.toString().trim() == '')) return -1;
  if ((value2 === null) || (value2.toString().trim() == '')) return 1;

  // Check NOT NULL Values
  if (!isNaN(parseFloat(value1)) && !isNaN(parseFloat(value2))) {
    return parseFloat(value1) - parseFloat(value2);
  }
  else return value1.toString().localeCompare(value2.toString());
}

function compare_execution_time(value1, value2) {
  // Check NULL & Empty Values
  if ((value1 === null && value2 === null) || (value1 !== null && value2 !== null && value1.toString().trim() == '' && value2.toString().trim() == '')) return 0;
  if ((value1 === null) || (value1.toString().trim() == '')) return -1;
  if ((value2 === null) || (value2.toString().trim() == '')) return 1;

  // Check NOT NULL Values
  return parseFloat(value1.toString().substring(0, value1.toString().length - 1)) - parseFloat(value2.toString().substring(0, value2.toString().length - 1));
}

// ##############################################################################################
// ERRORS
// ##############################################################################################
var errors_shown = false;

$("#errors-button").click(function () {
  if (!errors_shown) show_errors();
  else hide_errors();
});

function show_errors() {
  errors_shown = true;
  $("#errors-button").addClass("is-loading");

  setTimeout(function () {
    // Compile Errors
    var data = compile_errors(DATA);
    // Set New Data
    gridOptions.api.setRowData(data);
    // Set Order
    var sort = [{ colId: 'count', sort: 'desc' }];
    gridOptions.api.setSortModel(sort);
    // Disable Components
    $("#settings-button").attr("disabled", true);
    $("#filter-button").attr("disabled", true);
    $("#transformation-button").attr("disabled", true);
    // Change Error Button Class
    $("#errors-button").removeClass("is-loading");
    $("#errors-button").removeClass("is-info");
    $("#errors-button").addClass("is-warning");
    // Resize All Columns
    autoSizeAll();
  }, 100);
}

function hide_errors() {
  errors_shown = 0;
  $("#errors-button").addClass("is-loading");

  setTimeout(function () {
    // Re-initialize Grid with Default Columns & Data
    gridOptions.api.setColumnDefs(columnDefs);
    gridOptions.api.setRowData(DATA);
    // Apply Matching Columns
    apply_settings_modal();
    // Apply Current Filter
    filter_data();
    // Enable Components
    $("#settings-button").attr("disabled", false);
    $("#filter-button").attr("disabled", false);
    $("#transformation-button").attr("disabled", false);
    // Change Error Button Class
    $("#errors-button").removeClass("is-loading");
    $("#errors-button").removeClass("is-warning");
    $("#errors-button").addClass("is-info");
    // Resize All Columns
    autoSizeAll();
  }, 100);
}

function compile_errors(data) {
  var new_columns = [];
  var new_data = [];

  // Rebuild Columns
  var columns = ['Query', 'Error', 'Count', 'Databases'];
  for (var i = 0; i < columns.length; ++i) {
    new_columns.push({
      headerName: columns[i],
      field: columns[i].toLowerCase(),
      valueGetter: function (params) {
        var col_name = params.colDef.field;
        var value = params.data[col_name];
        return value;
      },
      comparator: compare_values
    });
  }
  // Rebuild Data
  for (var i = 0; i < data.length; ++i) {
    var row = data[i];
    // Rebuild Data
    if (row['meteor_status'] == '0') {
      var error_found = false;
      for (var j = 0; j < new_data.length; ++j) {
        if (new_data[j]['query'].localeCompare(row['meteor_query']) == 0 && new_data[j]['error'].localeCompare(row['meteor_response']) == 0) {
          // Error already exists
          new_data[j]['count'] = (parseInt(new_data[j]['count']) + 1).toString();

          // Check if database already exists
          var database_found = false;
          for (var k = 0; k < new_data[j]['databases'].length; ++k) {
            if (new_data[j]['databases'][k].localeCompare(row['meteor_database']) == 0) {
              database_found = true;
              break;
            }
          }
          if (!database_found) new_data[j]['databases'].push(row['meteor_database']);

          error_found = true;
          break;
        }
      }
      if (!error_found) {
        new_data.push({ 'query': row['meteor_query'], 'error': row['meteor_response'], 'count': '1', 'databases': [row['meteor_database']] })
      }
    }
  }
  // Sort Databases
  for (var i = 0; i < new_data.length; ++i) {
    new_data[i]['databases'].sort()
  }

  // Set New Columns
  gridOptions.api.setColumnDefs(new_columns);

  // Return new Grid Data
  return new_data;
}

// ##############################################################################################
// EXPORT MODAL
// ##############################################################################################
$("#export-button").click(function () {
  // Enable All Export Modal Objects
  enable_export_modal(true);
  // Show Export Modal
  $("#export-modal").addClass("is-active");
});

$("#export-modal-close").click(function () {
  enable_export_modal(false);
  close_export_modal();
});

$("#export-modal-cancel").click(function () {
  enable_export_modal(false);
  close_export_modal();
});

$("#export-modal-save").click(function () {
  enable_export_modal(false);
  // Add Button Loading Effect
  $("#export-modal-save").addClass("is-loading");
  setTimeout(function () {
    // Export data
    export_data();
    // Remove Button Loading Effect
    $("#export-modal-save").removeClass("is-loading");
    // Hide Export Modal
    close_export_modal();
  }, 10);
});

function close_export_modal() {
  $("#export-modal").removeClass('fadeIn');
  $("#export-modal").addClass('fadeOut');
  setTimeout(function () {
    $("#export-modal").removeClass("is-active");
    $("#export-modal").removeClass('fadeOut');
    $("#export-modal").addClass('fadeIn');
  }, 300);
}

function enable_export_modal(option) {
  // Enable/Disable All Export Modal Objects
  $('#export-format').attr("disabled", !option);
  $("#export-modal-cancel").attr('disabled', !option);
  $("#export-modal-close").attr('disabled', !option);
  $("#export-modal-save").attr('disabled', !option);
}

function export_data() {
  var export_value = $("#export-format").val();

  // Get Displayed Rows
  var rows_to_export = [];

  for (var i = 0; i < gridOptions.api.getDisplayedRowCount(); ++i) {
    try {
      var row = gridOptions.api.getDisplayedRowAtIndex(i)['data'];
      rows_to_export.push(row);
    }
    catch (err) { }
  }

  // Get Columns
  var displayed_columns = gridOptions.columnApi.getAllDisplayedColumns();
  var columns_to_export = [];
  for (var i = 0; i < displayed_columns.length; ++i) columns_to_export.push(displayed_columns[i]['colId']);

  // Get Columns to Remove
  var columns_to_remove = [];
  for (var i = 0; i < COLUMNS.length; ++i) {
    var to_remove = true;
    for (var j = 0; j < columns_to_export.length; ++j) {
      if (COLUMNS[i] == columns_to_export[j]) to_remove = false;
    }
    if (to_remove) columns_to_remove.push(COLUMNS[i]);
  }

  // Get Rows
  for (var i = 0; i < rows_to_export.length; ++i) {
    for (var j = 0; j < columns_to_remove.length; ++j) {
      delete rows_to_export[i][columns_to_remove[j]];
    }
  }

  // Check if there's any rows to export
  var nrows = rows_to_export.length;
  if (nrows == 0) show_error('No Rows', 'There are no rows to export. Please change your filter settings.', '');
  else {
    if (export_value == "meteor") export_meteor(rows_to_export, columns_to_export);
    else if (export_value == "json") export_json(rows_to_export);
    else if (export_value == "csv") export_csv(rows_to_export);
  }
}

function export_meteor(rows_to_export, columns_to_export) {
  // Generate Meteor Download File
  let export_data = {"DATA":{},"COLUMNS":{}}
  export_data['DATA'] = rows_to_export
  export_data['COLUMNS'] = columns_to_export
  if (INFO !== undefined) export_data['INFO'] = INFO
  download('meteor.json', JSON.stringify(export_data))
}

function export_json(rows_to_export) {
  // Generate Json Download File
  download('meteor.json', JSON.stringify(rows_to_export));
}

function export_csv(rows_to_export) {
  // Generate CSV Download File
  const replacer = (key, value) => value === null ? '' : value; // specify how you want to handle null values here
  const header = Object.keys(rows_to_export[0]);
  let csv = rows_to_export.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','));
  csv.unshift(header.join(','));
  csv = csv.join('\r\n');

  download('meteor.csv', csv);
}

function download(filename, text) {
  var element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
  element.setAttribute('download', filename);

  element.style.display = 'none';
  document.body.appendChild(element);

  element.click();

  document.body.removeChild(element);
}

// ##############################################################################################
// ERROR MODAL
// ##############################################################################################

$("#error-modal-close").click(function () {
  $("#error-modal").removeClass("is-active");
});

$("#error-modal-accept").click(function () {
  $("#error-modal").removeClass("is-active");
});

function show_error(title, message, code) {
  $("#import-button").removeClass("is-loading");
  $("#error-title").text(title);
  $("#error-message-body").html('<p>' + message + '</p>');
  $("#error-message-code").html('<p>' + code + '</p>');
  if (code.length == 0) $("#error-message-code").hide();
  else $("#error-message-code").show();
  $("#error-modal").addClass("is-active");
}

// ##############################################################################################
// THEMES (LIGHT / DARK)
// ##############################################################################################
function init_theme() {
  // if (getCookie('theme') == 'light') apply_light_theme();
  apply_dark_theme();
}

$("#theme-button").click(function () {
  if (THEME == 'light') {
    apply_dark_theme();
  }
  else if (THEME == 'dark') {
    apply_light_theme();
  }
});

function apply_light_theme() {
  // Set new Transition Theme
  THEME = 'light';

  // Store Theme to a Cookie
  // setCookie('theme', 'light', 365)

  // Change Button Title
  document.getElementById("theme-button").setAttribute('title', 'Dark Mode');

  // Body
  document.body.style.color = '#4a4a4a';
  document.body.style.backgroundColor = '#f9fcff';

  // Scrollbar - Firefox
  document.documentElement.style.setProperty('scrollbar-color', 'auto');
  // Scrollbar - Chrome
  document.documentElement.classList.remove("dark_scrollbar");
  // Scrollbar - Chrome (AG-GRID)
  apply_light_theme_scrollbar();

  // Input
  add_style(document.getElementsByClassName("input"), 'backgroundColor', '#fff');
  add_style(document.getElementsByClassName("input"), 'borderColor', '#b5b5b5');
  add_style(document.getElementsByClassName("input"), 'color', '#363636');

  // Loading
  document.getElementById("loading").style.backgroundColor = '#fff';
  document.getElementById("loading").style.color = '#4a4a4a';
  document.getElementById("loading").style.border = '1px solid #ced4da';

  // AG-GRID
  document.getElementById("bestHtml5Grid").style.border = '1px solid #ced4da';
  add_style(document.getElementsByClassName("stage-scenarios"), 'backgroundColor', '#f9fcff');
  add_style(document.getElementsByClassName("ag-theme-material"), 'backgroundColor', '#fff');
  add_style(document.getElementsByClassName("ag-theme-material"), 'color', 'rgba(0,0,0,0.87)');
  add_style(document.getElementsByClassName("ag-header"), 'backgroundColor', '#fff');
  add_style(document.getElementsByClassName("ag-header"), 'color', 'rgba(0,0,0,0.54)');
  add_style(document.getElementsByClassName("ag-header"), 'borderBottom', '1px solid #e2e2e2');
  remove_style(document.querySelectorAll(".ag-theme-material,.ag-header-cell,.ag-theme-material,.ag-header-group-cell,.ag-row"), 'border-color');
  remove_style(document.querySelectorAll(".ag-theme-material,.ag-header-cell,.ag-theme-material,.ag-header-group-cell,.ag-row"), 'background-color');
  remove_style(document.getElementsByClassName("ag-row-no-focus"), 'background-color');
  add_style(document.getElementsByClassName("ag-row-no-focus"), 'backgroundColor', '#fff');
  add_style(document.getElementsByClassName("ag-row-selected"), 'backgroundColor', '#eee');
  add_style(document.getElementsByClassName("ag-row-animation"), 'backgroundColor', '#fff');
  remove_class(document.getElementsByClassName("ag-row"), 'dark-row');
  add_class(document.getElementsByClassName("ag-row"), 'light-row');

  // AG-GRID - Column Hover Styles
  remove_hover(document.querySelectorAll('.ag-header-group-cell,.ag-header-cell'));
  // AG-GRID - Column Icons (sort and filter)
  remove_style(document.getElementsByClassName("ag-icon"), 'filter');
  // AG-GRID - New Generated Virtual Rows Style
  if (typeof gridOptions !== 'undefined') gridOptions.rowClass = 'light-row';
  // AG-GRID - Pinned Columns
  add_style(document.querySelectorAll(".ag-theme-material .ag-ltr .ag-row.ag-cell-last-left-pinned, .ag-theme-material .ag-ltr .ag-cell:not(.ag-cell-focus).ag-cell-last-left-pinned"), 'borderRight', '1px solid #e2e2e2');
  add_style(document.querySelectorAll(".ag-theme-material .ag-pinned-left-header"), 'borderRight', '1px solid #e2e2e2');

  // Modals
  add_style(document.getElementsByClassName("modal-card-head"), 'backgroundColor', '#f5f5f5');
  add_style(document.getElementsByClassName("modal-card-head"), 'borderBottom', '1px solid #dbdbdb');
  document.getElementById("error-modal-card-head").style.backgroundColor = '#ff3860';
  add_style(document.getElementsByClassName("modal-card-title"), 'color', '#363636');
  add_style(document.getElementsByClassName("modal-card-body"), 'backgroundColor', '#fff');
  add_style(document.getElementsByClassName("subtitle"), 'color', '#4a4a4a');
  add_style(document.querySelectorAll(".subtitle strong"), 'color', '#4a4a4a');
  add_style(document.getElementsByClassName("modal-card-foot"), 'backgroundColor', '#f5f5f5');
  add_style(document.getElementsByClassName("modal-card-foot"), 'borderTop', '1px solid #dbdbdb');
  document.getElementById("info-modal-save").classList.remove('is-light');
  document.getElementById("settings-modal-cancel").classList.remove('is-light');
  document.getElementById("filter-modal-cancel").classList.remove('is-light');
  document.getElementById("transformation-modal-cancel").classList.remove('is-light');
  document.getElementById("export-modal-cancel").classList.remove('is-light');
  document.getElementById("error-title").style.color = '#dcdcde';
  document.getElementById("error-modal-accept").classList.remove('is-light');
  document.getElementById("error-message-code").style.backgroundColor = '#f5f5f5';
  document.getElementById("error-message-code").style.border = '1px solid #ccc';
  document.getElementById("error-message-code").style.color = '#333';

  // Select2
  apply_light_theme_select2();
}

function apply_light_theme_scrollbar() {
  var components = document.querySelectorAll(".ag-body-viewport,.ag-body-horizontal-scroll-viewport,.ag-horizontal-left-spacer");
  for (var i = 0; i < components.length; ++i) {
    components[i].classList.remove("dark_scrollbar");
    components[i].style.overflow = 'hidden';
  }
  setTimeout(function () {
    for (var i = 0; i < components.length; ++i) {
      components[i].style.overflow = 'auto';
    }
  }, 100);

  var component = document.getElementsByClassName("ag-horizontal-left-spacer")
  if (component.length > 0) component[0].style.borderRight = '1px solid #e2e2e2';
}

function apply_light_theme_select2() {
  remove_style(document.getElementsByClassName("select2-selection--single"), 'background-color');
  add_style(document.getElementsByClassName("select2-selection__rendered"), 'color', '#444');
  remove_style(document.getElementsByClassName("select2-results"), 'backgroundColor');
  var select_elements = document.getElementsByClassName("js-example-basic-single");
  for (var i = 0; i < select_elements.length; i++) {
    $(select_elements[i]).unbind('select2:open');
    $(select_elements[i]).on('select2:open', __select2_apply_theme);
  }
}

function apply_dark_theme() {
  // Set new Transition Theme
  THEME = 'dark';

  // Store Theme to a Cookie
  // setCookie('theme', 'dark', 365)

  // Change Button Title
  document.getElementById("theme-button").setAttribute('title', 'Light Mode');

  // Body
  document.body.style.color = '#dcdcde';
  document.body.style.backgroundColor = '#373540';

  // Scrollbar - Firefox
  document.documentElement.style.setProperty('scrollbar-color', '#373540 #4f4d56');
  // Scrollbar - Chrome
  document.documentElement.classList.add("dark_scrollbar");
  // Scrollbar - Chrome (AG-GRID)
  apply_dark_theme_scrollbar();

  // Input
  add_style(document.getElementsByClassName("input"), 'backgroundColor', '#303843');
  add_style(document.getElementsByClassName("input"), 'borderColor', '#4f4d56');
  add_style(document.getElementsByClassName("input"), 'color', '#dcdcde');

  // Loading
  document.getElementById("loading").style.backgroundColor = '#373540';
  document.getElementById("loading").style.color = '#dcdcde';
  document.getElementById("loading").style.border = '1px solid #4f4d56';

  // AG-GRID
  document.getElementById("bestHtml5Grid").style.border = '1px solid #4f4d56';
  add_style(document.getElementsByClassName("stage-scenarios"), 'backgroundColor', '#373540');
  add_style(document.getElementsByClassName("ag-theme-material"), 'backgroundColor', '#373540');
  add_style(document.getElementsByClassName("ag-theme-material"), 'color', '#dcdcde');
  add_style(document.getElementsByClassName("ag-header"), 'backgroundColor', '#3a3843');
  add_style(document.getElementsByClassName("ag-header"), 'color', 'rgba(255,255,255,0.8)');
  add_style(document.getElementsByClassName("ag-header"), 'borderBottom', '1px solid #4f4d56');
  add_style(document.querySelectorAll(".ag-theme-material,.ag-header-cell,.ag-theme-material,.ag-header-group-cell,.ag-row"), 'borderColor', '#4f4d56');
  add_style(document.getElementsByClassName("ag-row-no-focus"), 'backgroundColor', '#3a3843');
  add_style(document.getElementsByClassName("ag-row-no-focus"), 'borderColor', '#4f4d56');
  add_style(document.getElementsByClassName("ag-row-selected"), 'backgroundColor', '#303843');
  add_style(document.getElementsByClassName("ag-row-animation"), 'backgroundColor', '#3a3843');
  remove_class(document.getElementsByClassName("ag-row"), 'light-row');
  add_class(document.getElementsByClassName("ag-row"), 'dark-row');

  // AG-GRID - Column Hover
  add_hover(document.querySelectorAll('.ag-header-group-cell,.ag-header-cell'));
  // AG-GRID - Column Icons (sort and filter)
  add_style(document.getElementsByClassName("ag-icon"), 'filter', 'invert(100%)');
  // AG-GRID - New Generated Virtual Rows Style
  if (typeof gridOptions !== 'undefined') gridOptions.rowClass = 'dark-row';
  // AG-GRID - Pinned Columns
  add_style(document.querySelectorAll(".ag-theme-material .ag-ltr .ag-row.ag-cell-last-left-pinned, .ag-theme-material .ag-ltr .ag-cell:not(.ag-cell-focus).ag-cell-last-left-pinned"), 'borderRight', '1px solid #4f4d56');
  add_style(document.querySelectorAll(".ag-theme-material .ag-pinned-left-header"), 'borderRight', '1px solid #4f4d56');

  // Modals
  add_style(document.getElementsByClassName("modal-card-head"), 'backgroundColor', '#303843');
  add_style(document.getElementsByClassName("modal-card-head"), 'borderBottom', '1px solid #4f4d56');
  document.getElementById("error-modal-card-head").style.backgroundColor = '#ff3860';
  add_style(document.getElementsByClassName("modal-card-title"), 'color', '#dcdcde');
  add_style(document.getElementsByClassName("modal-card-body"), 'backgroundColor', '#3a3843');
  add_style(document.getElementsByClassName("subtitle"), 'color', '#dcdcde');
  add_style(document.querySelectorAll(".subtitle strong"), 'color', '#dcdcde');
  add_style(document.getElementsByClassName("modal-card-foot"), 'backgroundColor', '#303843');
  add_style(document.getElementsByClassName("modal-card-foot"), 'borderTop', '1px solid #4f4d56');
  document.getElementById("info-modal-save").classList.add('is-light');
  document.getElementById("settings-modal-cancel").classList.add('is-light');
  document.getElementById("filter-modal-cancel").classList.add('is-light');
  document.getElementById("transformation-modal-cancel").classList.add('is-light');
  document.getElementById("export-modal-cancel").classList.add('is-light');
  document.getElementById("error-modal-accept").classList.add('is-light');
  document.getElementById("error-message-code").style.backgroundColor = '#303843';
  document.getElementById("error-message-code").style.border = '1px solid #4f4d56';
  document.getElementById("error-message-code").style.color = '#dcdcde';

  // Select2
  apply_dark_theme_select2();
}

function apply_dark_theme_scrollbar() {
  var components = document.querySelectorAll(".ag-body-viewport,.ag-body-horizontal-scroll-viewport,.ag-horizontal-left-spacer");
  for (var i = 0; i < components.length; ++i) {
    components[i].classList.add("dark_scrollbar");
    components[i].style.overflow = 'hidden';
  }
  setTimeout(function () {
    for (var i = 0; i < components.length; ++i) {
      components[i].style.overflow = 'auto';
    }
  }, 100);

  var component = document.getElementsByClassName("ag-horizontal-left-spacer")
  if (component.length > 0) component[0].style.borderRight = '1px solid #4f4d56';
}

function apply_dark_theme_select2() {
  add_style(document.getElementsByClassName("select2-selection--single"), 'backgroundColor', '#3a3843');
  add_style(document.getElementsByClassName("select2-selection__rendered"), 'color', '#dcdcde');
  var select_elements = document.getElementsByClassName("js-example-basic-single");
  for (var i = 0; i < select_elements.length; i++) {
    $(select_elements[i]).unbind('select2:open');
    $(select_elements[i]).on('select2:open', __select2_apply_theme);
  }
}

function __select2_apply_theme() {
  if (THEME == 'light') {
    add_style(document.getElementsByClassName("select2-results"), 'backgroundColor', '#fff');
    add_style(document.getElementsByClassName("select2-search__field"), 'backgroundColor', '#fff');
    add_style(document.getElementsByClassName("select2-search__field"), 'color', '#4a4a4a');
    add_style(document.getElementsByClassName("select2-search--dropdown"), 'backgroundColor', '#fff');
    setTimeout(function () {
      add_style(document.querySelectorAll('.select2-container--default .select2-results__option[aria-selected="true"]'), 'backgroundColor', '#ddd');
    }, 1);

  }
  else if (THEME == 'dark') {
    add_style(document.getElementsByClassName("select2-results"), 'backgroundColor', '#3a3843');
    add_style(document.getElementsByClassName("select2-search__field"), 'backgroundColor', '#4f4d56');
    add_style(document.getElementsByClassName("select2-search__field"), 'color', '#dcdcde');
    add_style(document.getElementsByClassName("select2-search--dropdown"), 'backgroundColor', '#3a3843');
    setTimeout(function () {
      add_style(document.querySelectorAll('.select2-container--default .select2-results__option[aria-selected="true"]'), 'backgroundColor', '#4f4d56');
    }, 1);
  }
}

function onSelectionChanged() {
  if (THEME == 'light') {
    add_style(document.getElementsByClassName("ag-row-no-focus"), 'backgroundColor', '#fff');
    remove_style(document.getElementsByClassName("ag-row-no-focus"), 'background-color');
    add_style(document.getElementsByClassName("ag-row-selected"), 'backgroundColor', '#eee');
  }
  else if (THEME == 'dark') {
    add_style(document.getElementsByClassName("ag-row-no-focus"), 'backgroundColor', '#3a3843');
    remove_style(document.getElementsByClassName("ag-row-no-focus"), 'background-color');
    add_style(document.getElementsByClassName("ag-row-selected"), 'backgroundColor', '#303843');
  }
}

var cellEditing;

function onCellEditingStarted() {
  if (THEME == 'dark') {
    cellEditing = document.querySelectorAll(".ag-theme-material .ag-cell-inline-editing");
    add_style(cellEditing, 'backgroundColor', '#3a3843');
    document.getElementsByClassName("ag-input-text-wrapper")[0].firstChild.style.color = '#dcdcde';
  }
}

function onCellEditingStopped() {
  if (THEME == 'dark') cellEditing[0].style.removeProperty('background-color');
}

function onVirtualColumnsChanged() {
  if (THEME == 'light') {
    remove_style(document.querySelectorAll(".ag-theme-material,.ag-header-cell,.ag-theme-material,.ag-header-group-cell,.ag-row"), 'border-color');
    remove_hover(document.querySelectorAll('.ag-header-group-cell,.ag-header-cell'));
  }
  else if (THEME == 'dark') {
    add_style(document.querySelectorAll(".ag-theme-material,.ag-header-cell,.ag-theme-material,.ag-header-group-cell,.ag-row"), 'borderColor', '#4f4d56');
    add_hover(document.querySelectorAll('.ag-header-group-cell,.ag-header-cell'));
    add_style(document.getElementsByClassName("ag-header"), 'backgroundColor', '#3a3843');
    add_style(document.getElementsByClassName("ag-header"), 'color', 'rgba(255,255,255,0.8)');
    add_style(document.getElementsByClassName("ag-header"), 'borderBottom', '1px solid #4f4d56');
    add_style(document.getElementsByClassName("ag-icon"), 'filter', 'invert(100%)');
    // Pinned Columns
    add_style(document.querySelectorAll(".ag-theme-material .ag-ltr .ag-row.ag-cell-last-left-pinned, .ag-theme-material .ag-ltr .ag-cell:not(.ag-cell-focus).ag-cell-last-left-pinned"), 'borderRight', '1px solid #4f4d56');
    add_style(document.querySelectorAll(".ag-theme-material .ag-pinned-left-header"), 'borderRight', '1px solid #4f4d56');
  }
}

function onViewportChanged() {
  // AG-GRID - Pinned Columns
  if (THEME == 'dark') {
    add_style(document.querySelectorAll(".ag-theme-material .ag-ltr .ag-row.ag-cell-last-left-pinned, .ag-theme-material .ag-ltr .ag-cell:not(.ag-cell-focus).ag-cell-last-left-pinned"), 'borderRight', '1px solid #4f4d56');
    add_style(document.querySelectorAll(".ag-theme-material .ag-pinned-left-header"), 'borderRight', '1px solid #4f4d56');
  }
  else if (THEME == 'light') {
    add_style(document.querySelectorAll(".ag-theme-material .ag-ltr .ag-row.ag-cell-last-left-pinned, .ag-theme-material .ag-ltr .ag-cell:not(.ag-cell-focus).ag-cell-last-left-pinned"), 'borderRight', '1px solid #e2e2e2');
    add_style(document.querySelectorAll(".ag-theme-material .ag-pinned-left-header"), 'borderRight', '1px solid #e2e2e2');
  }
}

function onDragStarted() {
  if (THEME == 'light') add_style(document.getElementsByClassName("ag-header-cell-moving"), 'background-color', '#f2f2f2');
  else if (THEME == 'dark') add_style(document.getElementsByClassName("ag-header-cell-moving"), 'background-color', '#209cee');
}

function onColumnMoved() {
  if (THEME == 'light') add_style(document.getElementsByClassName("ag-header-cell-moving"), 'background-color', '#f2f2f2');
  else if (THEME == 'dark') add_style(document.getElementsByClassName("ag-header-cell-moving"), 'background-color', '#209cee');
}

function add_hover(components) {
  for (var i = 0; i < components.length; i++) {
    components[i].addEventListener('mouseover', __mouseover);
    components[i].addEventListener('mouseout', __mouseout);
  }
}

function remove_hover(components) {
  for (var i = 0; i < components.length; i++) {
    components[i].removeEventListener('mouseover', __mouseover);
    components[i].removeEventListener('mouseout', __mouseout);
  }
}

function __mouseover() {
  this.style.backgroundColor = 'rgba(0,0,0,0.2)';
}

function __mouseout() {
  this.style.removeProperty('background-color');
}

function add_style(components, style_class, value) {
  for (var i = 0; i < components.length; i++) {
    components[i].style[style_class] = value.toString();
  }
}

function remove_style(components, style_class) {
  for (var i = 0; i < components.length; i++) {
    components[i].style.removeProperty(style_class);
  }
}


function add_class(components, class_name) {
  for (var i = 0; i < components.length; i++) {
    components[i].classList.add(class_name);
  }
}

function remove_class(components, class_name) {
  for (var i = 0; i < components.length; i++) {
    components[i].classList.remove(class_name);
  }
}

// ##############################################################################################
// COOKIES
// ##############################################################################################
function getCookie(cname) {
  var name = cname + "=";
  var ca = document.cookie.split(';');
  for (var i = 0; i < ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

function setCookie(cname, cvalue, exdays) {
  var d = new Date();
  d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
  var expires = "expires=" + d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

// ##############################################################################################
// METEOR-NEXT
// ##############################################################################################
function initMeteorNext() {
  $("#loading").html('');
  $("#import-div").remove();
  $("#import-div-separator").remove();
  $("#loading").append("<p>- Retrieving Data ...</p>");
}
function showError(title, description) {
  $("#loading").html('');
  var title_message = title // "Authorized Access Only";
  var error_message = description // "The URL provided is private"
  show_error(title_message, error_message, '');
}
function loadMeteorNext(data) {
  try {
    // Init variables
    var error_title = "Invalid File Type";
    var error_message = "Please use a <b>Meteor</b> file format. Example of a <b>meteor.json</b> file:<br><br>";
    var error_code = `{<br>
      &nbsp "DATA": [["row1_col1", "row1_col2"],["row2_col1", "row2_col2"]],<br>
      &nbsp "COLUMNS": ["column1", "column2"]<br>
    }`;
    IMPORT_FILE = data
    // Check Errors
    var valid_file = false;
    if (!('DATA' in IMPORT_FILE)) show_error(error_title, error_message, error_code);
    else if (!('COLUMNS' in IMPORT_FILE)) show_error(error_title, error_message, error_code);
    else valid_file = true;
  }
  catch (err) {
    show_error(error_title, error_message, error_code);
  }
  if (valid_file) {
    // Init Meteor Core 
    setTimeout(function () { init_meteor(); }, 100);
  }
}