<template>
  <div style="height:100%">
    <!------------->
    <!-- COLUMNS -->
    <!------------->
    <div style="height:calc(100% - 84px)">
      <ag-grid-vue ref="agGridStructureColumns" @grid-ready="onGridReady" @new-columns-loaded="onNewColumnsLoaded" @cell-key-down="onCellKeyDown" @row-double-clicked="onRowDoubleClicked" @row-drag-end="onRowDragEnd" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowDragManaged="true" suppressMoveWhenRowDragging="true" rowHeight="35" headerHeight="35" rowSelection="single" rowDeselection="true" stopEditingWhenGridLosesFocus="true" :columnDefs="structureHeaders.columns" :rowData="structureItems.columns"></ag-grid-vue>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn @click="addColumn" text small title="New Column" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="removeColumn" text small title="Remove Column" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="refreshColumns" text small title="Refresh Columns" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            <v-icon v-if="bottomBar.structure.columns['status'] == 'success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:5px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBar.structure.columns['status'] == 'failure'" title="Failed" small style="color:rgb(231, 76, 60); padding-bottom:1px; padding-right:5px;">fas fa-times-circle</v-icon>
            <span :title="bottomBar.structure.columns['text']">{{ bottomBar.structure.columns['text'] }}</span>
          </div>
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBar.structure.columns['info'] }}</div>
        </v-col>
      </v-row>
    </div>
    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="dialog" persistent max-width="60%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ dialogTitle }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <div v-if="dialogText.length > 0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogText }}</div>
                  <div v-if="Object.keys(dialogItem).length > 0">
                    <v-text-field v-model="dialogItem.name" :rules="[v => !!v || '']" label="Name" autofocus required style="padding-top:0px;"></v-text-field>
                    <v-autocomplete v-model="dialogItem.type" :items="server.columnTypes" :rules="[v => !!v || '']" label="Type" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                    <v-text-field v-model="dialogItem.length" label="Length" required style="padding-top:0px;"></v-text-field>
                    <v-autocomplete :disabled="!['CHAR','VARCHAR','TEXT','TINYTEXT','MEDIUMTEXT','LONGTEXT','SET','ENUM'].includes(dialogItem.type)" v-model="dialogItem.collation" :items="server.collations" label="Collation" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                    <v-text-field :disabled="dialogItem.auto_increment" v-model="dialogItem.default" label="Default" required style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="dialogItem.comment" label="Comment" required style="padding-top:0px;"></v-text-field>
                    <v-checkbox :disabled="!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT','DECIMAL','FLOAT','DOUBLE'].includes(dialogItem.type)" v-model="dialogItem.unsigned" label="Unsigned" color="info" style="margin-top:0px; padding-top:0px;" hide-details></v-checkbox>
                    <v-checkbox :disabled="!['DATETIME','TIMESTAMP'].includes(dialogItem.type)" v-model="dialogItem.current_timestamp" label="On Update Current Timestamp" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                    <v-checkbox :disabled="!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT'].includes(dialogItem.type)" v-model="dialogItem.auto_increment" label="Auto Increment" @change="dialogItem.auto_increment ? dialogItem.default = '' : ''" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                    <v-checkbox v-model="dialogItem.null" label="Allow Null" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col v-if="dialogSubmitText.length > 0" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="dialogSubmit" color="primary">{{ dialogSubmitText }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogCancelText.length > 0" style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialog = false" outlined color="#e74d3c">{{ dialogCancelText }}</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import {AgGridVue} from "ag-grid-vue";
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      // Loading
      loading: false,
      // Dialog
      dialog: false,
      dialogMode: '',
      dialogItem: {},
      dialogTitle: '',
      dialogText: '',
      dialogSubmitText: '',
      dialogCancelText: ''
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'gridApi',
      'columnApi',
      'structureHeaders',
      'structureItems',
      'treeviewSelected',
      'server',
      'bottomBar',
      'tabStructureSelected',
    ], { path: 'client/connection' }),
  },
  watch: {
    dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
    },
    tabStructureSelected(val) {
      this.$nextTick(() => {
        if (val == 'columns') this.resizeTable()
      })
    }
  },
  methods: {
    onGridReady(params) {
      this.gridApi.structure.columns = params.api
      this.columnApi.structure.columns = params.columnApi
      this.$refs['agGridStructureColumns'].$el.addEventListener('click', this.onGridClick)
      this.gridApi.structure.columns.showLoadingOverlay()
    },
    onNewColumnsLoaded() {
      if (this.gridApi.structure.columns != null) this.resizeTable()
    },
    onGridClick(event) {
      if (event.target.className == 'ag-center-cols-viewport') {
        this.gridApi.structure.columns.deselectAll()
      }
    },
    resizeTable() {
      var allColumnIds = [];
      this.columnApi.structure.columns.getAllColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi.structure.columns.autoSizeColumns(allColumnIds);
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        navigator.clipboard.writeText(e.value)

        // Highlight cells
        e.event.originalTarget.classList.add('ag-cell-highlight');
        e.event.originalTarget.classList.remove('ag-cell-highlight-animation')

        // Add animation
        window.setTimeout(function () {
            e.event.originalTarget.classList.remove('ag-cell-highlight')
            e.event.originalTarget.classList.add('ag-cell-highlight-animation')
            e.event.originalTarget.style.transition = "background-color " + 200 + "ms"

            // Remove animation
            window.setTimeout(function () {
                e.event.originalTarget.classList.remove('ag-cell-highlight-animation')
                e.event.originalTarget.style.transition = null;
            }, 200);
        }, 200);
      }
    },
    onRowDoubleClicked(event) {
      this.editStructure(event.data)
    },
    onRowDragEnd(event) {
      if (event.overIndex - event.node.id == 0) return
      this.dialogMode = 'drag'
      this.dialogSubmit(event)
    },
    addColumn() {
      var dialogOptions = {
        mode: 'new',
        title: 'New Column',
        text: '',
        item: { name: '', type: '', length: '', collation: '', default: '', comment: '', null: false, unsigned: false, current_timestamp: false, auto_increment: false },
        submit: 'Save',
        cancel: 'Cancel'
      }
      this.showDialog(dialogOptions)
    },
    editColumn(data) {
      var dialogOptions = {
        mode: 'edit',
        title: 'Edit Column',
        text: '',
        item: {
          name: data.name, 
          type: data.type, 
          length: (data.length == null) ? '' : ['ENUM','SET'].includes(data.type) ? data.length.replaceAll("'",'') : data.length, 
          collation: (data.collation == null) ? '' : data.collation, 
          default: (data.default == null) ? '' : data.default, 
          comment: (data.comment == null) ? '' : data.comment, 
          null: data.allow_null, 
          unsigned: data.unsigned, 
          current_timestamp: data.extra.toLowerCase() == 'on update current_timestamp', 
          auto_increment: data.extra.toLowerCase() ==  'auto_increment'
        },
        submit: 'Save',
        cancel: 'Cancel'
      }
      this.showDialog(dialogOptions)
    },
    removeColumn() {
      this.dialogMode = 'delete'
      var dialogOptions = {
        mode: 'delete',
        title: 'Delete column?',
        text: "Are you sure you want to delete the column '" + this.gridApi.structure.columns.getSelectedRows()[0].Name + "' from this table? This action cannot be undone.",
        item: {},
        submit: 'Cancel',
        cancel: 'Delete'
      }
      this.showDialog(dialogOptions)
    },
    refreshColumns() {
      EventBus.$emit('GET_STRUCTURE')
    },
    dialogSubmit(event) {
      this.loading = true
      let query = 'ALTER TABLE ' + this.treeviewSelected['name']

      if (['new','edit'].includes(this.dialogMode)) {
        // Parse Form Fields
        if (!['CHAR','VARCHAR','TEXT','TINYTEXT','MEDIUMTEXT','LONGTEXT','ENUM','SET'].includes(this.dialogItem.type)) this.dialogItem.collation = ''
        if (!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT','DECIMAL','FLOAT','DOUBLE'].includes(this.dialogItem.type)) this.dialogItem.unsigned = false
        if (!['DATETIME','TIMESTAMP'].includes(this.dialogItem.type)) this.dialogItem.current_timestamp = false
        if (!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT'].includes(this.dialogItem.type)) this.dialogItem.auto_increment = false

        // Check if all fields are filled
        if (!this.$refs.dialogForm.validate()) {
          EventBus.$emit('NOTIFICATION', 'Please make sure all required fields are filled out correctly', 'error')
          this.loading = false
          return
        }

        // Build Query
        if (this.dialogMode == 'new') query += ' ADD ' + this.dialogItem.name
        else if (this.dialogMode == 'edit') query += ' CHANGE ' + this.gridApi.structure.columns.getSelectedRows()[0].Name  + ' ' + this.dialogItem.name
        query += ' ' + this.dialogItem.type 
          + (this.dialogItem.length.length > 0 ? (this.dialogItem.length.indexOf(',') == -1) ? '(' + this.dialogItem.length + ')' : '(' + this.dialogItem.length.split(",").map(item => "'" + item.trim() + "'") + ')' : '')
          + (this.dialogItem.unsigned ? ' UNSIGNED' : '')
          + (this.dialogItem.collation.length > 0 ? ' CHARACTER SET ' + this.dialogItem.collation.split('_')[0] + ' COLLATE ' + this.dialogItem.collation : '')
          + (this.dialogItem.null ? ' NULL' : ' NOT NULL')
          + (this.dialogItem.default.length > 0 ? " DEFAULT" + (this.dialogItem.default == 'CURRENT_TIMESTAMP' ? ' CURRENT_TIMESTAMP' : " '" + this.dialogItem.default + "'") : '')
          + (this.dialogItem.current_timestamp ? ' ON UPDATE CURRENT_TIMESTAMP' : '')
          + (this.dialogItem.auto_increment ? ' AUTO_INCREMENT' : '')
          + (this.dialogItem.comment ? " COMMENT '" + this.dialogItem.comment + "'" : '')
      }
      else if (this.dialogMode == 'delete') query += ' DROP COLUMN ' + this.gridApi.structure.columns.getSelectedRows()[0]['Name']
      else if (this.dialogMode == 'drag') {
        query += ' MODIFY ' + this.gridApi.structure.columns.getDisplayedRowAtIndex(event.node.rowIndex).data['Name']
          + ' ' + event.node.data['Type'] 
          + (event.node.data['Length'] !== null ? '(' + event.node.data['Length'] + ')' : '')
          + (event.node.data['Unsigned'] ? ' UNSIGNED' : '')
          + (event.node.data['Collation'] !== null ? ' CHARACTER SET ' + event.node.data['Collation'].split('_')[0] + ' COLLATE ' + event.node.data['Collation'] : '')
          + (event.node.data['Allow Null'] ? ' NULL' : ' NOT NULL')
          + (event.node.data['Default'] !== null ? " DEFAULT" + (event.node.data['Default'] == 'CURRENT_TIMESTAMP' ? ' CURRENT_TIMESTAMP' : " '" + event.node.data['Default'] + "'") : '')
          + (event.node.data['Extra'].toLowerCase() == 'on update current_timestamp' ? ' ON UPDATE CURRENT_TIMESTAMP' : '')
          + (event.node.data['Extra'].toLowerCase() ==  'auto_increment' ? ' AUTO_INCREMENT' : '')
          + (event.node.data['Comment'] ? " COMMENT '" + event.node.data['Comment'] + "'" : '')
          + (event.node.rowIndex == 0 ? ' FIRST' : ' AFTER ' + this.gridApi.structure.columns.getDisplayedRowAtIndex(event.node.rowIndex - 1).data['Name'])
      }
      query += ';'

      // Execute query
      this.execute(query)
    },
    execute(query) {
      let promise = new Promise((resolve, reject) => {
        EventBus.$emit('EXECUTE_STRUCTURE', query, resolve, reject)
      })
      promise.then(() => { this.dialog = false })
        .catch(() => {})
        .finally(() => { this.loading = false })
    },
    showDialog(options) {
      this.dialogMode = options.mode
      this.dialogTitle = options.title
      this.dialogText = options.text
      this.dialogItem = options.item
      this.dialogSubmitText = options.submit
      this.dialogCancelText = options.cancel
      this.dialog = true
    },
  }
}
</script>