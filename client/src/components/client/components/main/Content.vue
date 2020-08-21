<template>
  <div style="height:100%">
    <!------------->
    <!-- CONTENT -->
    <!------------->
    <div style="height:calc(100% - 36px)">
      <div style="width:100%; height:100%">
        <div style="height:45px; background-color:#303030; margin:0px;">
          <v-row no-gutters>
            <v-col sm="auto">
              <div class="body-2" style="margin-top:13px; padding-left:10px; padding-right:10px;">Search:</div>
            </v-col>
            <v-col cols="2">
              <v-select v-model="contentSearchColumn" :items="contentColumnsName" dense solo hide-details height="35px" style="padding-top:5px;"></v-select>
            </v-col>
            <v-col cols="2">
              <v-select v-model="contentSearchFilter" :items="contentSearchFilterItems" dense solo hide-details height="35px" style="padding-top:5px; padding-left:5px;"></v-select>
            </v-col>
            <v-col v-if="contentSearchFilter != 'BETWEEN'">
              <v-text-field @keyup.enter="filterClick" :disabled="['IS NULL','IS NOT NULL'].includes(contentSearchFilter)" v-model="contentSearchFilterText" solo dense hide-details prepend-inner-icon="search" height="35px" style="padding-top:5px; padding-left:5px;"></v-text-field>
            </v-col>
            <v-col v-if="contentSearchFilter == 'BETWEEN'">
              <v-text-field v-model="contentSearchFilterText" @keyup.enter="filterClick" solo dense hide-details prepend-inner-icon="search" height="35px" style="padding-top:5px; padding-left:5px;"></v-text-field>
            </v-col>
            <v-col v-if="contentSearchFilter == 'BETWEEN'" sm="auto">
              <div class="body-2" style="margin-top:13px; padding-left:10px; padding-right:5px;">AND</div>
            </v-col>
            <v-col v-if="contentSearchFilter == 'BETWEEN'">
              <v-text-field v-model="contentSearchFilterText2" @keyup.enter="filterClick" solo dense hide-details prepend-inner-icon="search" height="35px" style="padding-top:5px; padding-left:5px;"></v-text-field>
            </v-col>
            <v-col sm="auto" justify="end">
              <v-btn @click="filterClick" style="margin-top:4px; margin-left:6px; margin-right:5px;">Filter</v-btn>
            </v-col>
          </v-row>
        </div>
        <ag-grid-vue ref="agGridContent" suppressColumnVirtualisation @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" @selection-changed="onSelectionChanged" @row-clicked="onRowClicked" @cell-editing-started="cellEditingStarted($event, true)" @cell-editing-stopped="cellEditingStopped($event, true)" style="width:100%; height:calc(100% - 48px);" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" rowDeselection="true" :stopEditingWhenGridLosesFocus="true" :columnDefs="contentHeaders" :rowData="contentItems"></ag-grid-vue>
      </div>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn @click="addRow" text small title="Add row" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="removeRow" :disabled="!isRowSelected" text small title="Remove selected row(s)" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="filterClick" text small title="Refresh rows" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="exportRows('content')" text small title="Export rows" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-arrow-down</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            <v-icon v-if="bottomBarContent['status']=='success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:5px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBarContent['status']=='failure'" title="Failed" small style="color:rgb(231, 76, 60); padding-bottom:1px; padding-right:5px;">fas fa-times-circle</v-icon>
            <span :title="bottomBarContent['text']">{{ bottomBarContent['text'] }}</span>
          </div>
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBarContent['info'] }}</div>
        </v-col>
      </v-row>
    </div>
    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="dialog" persistent max-width="50%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">{{ dialogTitle }}</div>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:20px; margin-bottom:15px;">
                  <div v-if="dialogText.length>0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogText }}</div>
                  <v-select v-if="dialogMode=='export'" outlined v-model="dialogSelect" :items="['Meteor','JSON','CSV','SQL']" label="Format" hide-details></v-select>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col v-if="dialogButtonText1.length > 0" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="dialogSubmit" color="primary">{{ dialogSubmitText }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogButtonText2.length > 0" style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialogCancel" outlined color="#e74d3c">{{ dialogCancelText }}</v-btn>
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
import axios from 'axios'

import {AgGridVue} from "ag-grid-vue";
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

export default {
  data() {
    return {
      dialog: false,
      dialogMode: '',
      dialogTitle: '',
      dialogText: '',
      dialogButtonText1: '',
      dialogButtonText2: '',
      loading: false,
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
        'contentHeaders',
        'contentItems',
        'treeviewSelected',
        'structureHeaders',
        'gridApi',
        'columnApi',
        'server',
        'database',
        'currentCellEditMode',
        'currentCellEditNode',
        'currentCellEditValues',
        'contentSearchFilter',
        'contentSearchFilterText',
        'contentSearchFilterText2',
        'contentSearchFilterItems',
        'contentSearchColumn',
        'contentColumnsName',
        'isRowSelected',
        'bottomBarContent'
    ], { path: 'client/connection' }),
  },
  mounted () {
    EventBus.$on('GET_CONTENT', this.getContent);
  },
  methods: {
   onGridReady(params) {
      this.gridApi.content = params.api
      this.columnApi.content = params.columnApi
      this.$refs['agGridContent'].$el.addEventListener('click', this.onGridClick)
      this.gridApi.content.showLoadingOverlay()
    },
    onGridClick(event) {
      if (event.target.className == 'ag-center-cols-viewport') {
        this.gridApi.content.deselectAll()
        this.cellEditingSubmit(this.currentCellEditMode, this.currentCellEditNode, this.currentCellEditValues)
      }
    },
    onSelectionChanged() {
      this.isRowSelected = this.gridApi.content.getSelectedNodes().length > 0
    },
    onRowClicked(event) {
      if (Object.keys(this.currentCellEditNode).length != 0 && this.currentCellEditNode.rowIndex != event.rowIndex) {
        this.cellEditingSubmit(this.currentCellEditMode, this.currentCellEditNode, this.currentCellEditValues)
      }
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
    getContent() {
      this.bottomBarContent = { status: '', text: '', info: '' }
      this.gridApi.content.showLoadingOverlay()
      const payload = {
        server: this.server.id,
        database: this.database,
        table: this.treeviewSelected['name'],
        queries: ['SELECT * FROM ' + this.treeviewSelected['name'] + ' LIMIT 1000;' ]
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          this.parseContentExecution(JSON.parse(response.data.data))          
        })
        .catch((error) => {
          this.gridApi.content.hideOverlay()
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    parseContentExecution(data) {
      // Build Data Table
      var headers = []
      var items = data[0]['data']
      // Build Headers
      if (data.length > 0) {
        this.contentColumnsName = data[0]['columns']['name']
        this.contentColumnsDefault = data[0]['columns']['default']
        this.contentColumnsType = data[0]['columns']['type']
        this.contentPks = data[0]['pks']
        this.contentSearchColumn = this.contentColumnsName[0].trim()
        for (let i = 0; i < this.contentColumnsName.length; ++i) {
          let field = this.contentColumnsName[i].trim()
          headers.push({ headerName: this.contentColumnsName[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: true, 
            valueGetter: function(params) {
              return (params.data[field] == null) ? 'NULL' : params.data[field]
            },
            cellClassRules: {
              'ag-cell-null': params => {
                return params.data[field] == null
              },
              'ag-cell-normal': function(params) {
                return params.data[field] != null
              }
            }
          })
        }
      }
      this.contentHeaders = []
      this.contentHeaders = headers
      this.contentItems = items
      this.gridApi.content.setRowData(items)
      this.isRowSelected = false

      // Resize Table
      this.gridApi.content.setColumnDefs(headers)
      this.resizeTable()

      // Build BottomBar
      this.parseContentBottomBar(data)
    },
    resizeTable() {
      var allColumnIds = [];
      this.columnApi.content.getAllColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi.content.autoSizeColumns(allColumnIds);
    },
    addRow() {
      // Clean vars
      this.currentCellEditValues = {}
      this.currentCellEditNode = {}
      this.currentCellEditMode = 'new'

      var newData = {}
      for (let i = 0; i < this.contentColumnsName.length; ++i) {
        newData[this.contentColumnsName[i]] = this.contentColumnsDefault[i]
      }

      var rowCount = this.gridApi.content.getDisplayedRowCount()
      var nodes = this.gridApi.content.getSelectedNodes()
      for (let i = 0; i < nodes.length; ++i) nodes[i].setSelected(false)

      this.gridApi.content.applyTransaction({ add: [newData] })
      this.gridApi.content.setFocusedCell(rowCount, this.contentColumnsName[0])
      var node = this.gridApi.content.getDisplayedRowAtIndex(rowCount)
      node.setSelected(true)
      this.gridApi.content.startEditingCell({
        rowIndex: rowCount,
        colKey: this.contentColumnsName[0]
      });
    },
    removeRow() {
      // Show confirmation dialog
      var dialogOptions = {
        'mode': 'removeRowConfirm',
        'title': 'Delete rows?',
        'text': 'Are you sure you want to delete the selected ' + this.gridApi.content.getSelectedNodes().length + ' rows from this table? This action cannot be undone.',
        'button1': 'Cancel',
        'button2': 'Delete'
      }
      this.showDialog(dialogOptions)
    },
    removeRowSubmit() {
      // Build Pks
      let nodes = this.gridApi.content.getSelectedNodes()
      let pks = []
      for (let i = 0; i < nodes.length; ++i) {
        let pk = []
        for (let j = 0; j < this.contentPks.length; ++j) {
          pk.push(this.contentPks[j] + " = '" + nodes[i].data[this.contentPks[j]] + "'")
        }
        pks.push('(' + pk.join(' AND ') + ')')
      }
      // Build Query
      var query = 'DELETE FROM ' + this.treeviewSelected['name'] + ' WHERE ' + pks.join(' OR ') + ';'
      // Show overlay
      this.gridApi.content.showLoadingOverlay()
      // Execute Query
      const payload = {
        server: this.server.id,
        database: this.database,
        queries: [query]
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          // Remove Frontend Rows
          this.gridApi.content.applyTransaction({ remove: this.gridApi.content.getSelectedRows() })
          // Build BottomBar
          this.parseContentBottomBar(JSON.parse(response.data.data))
          // Close Dialog
          this.dialog = false
        })
        .catch((error) => {
          this.gridApi.content.hideOverlay()
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else {
            // Show error
            let data = JSON.parse(error.response.data.data)
            let dialogOptions = {
              'mode': 'info',
              'title': 'Unable to delete row(s)',
              'text': data[0]['error'],
              'button1': 'Close',
              'button2': ''
            }
            this.showDialog(dialogOptions)
            // Build BottomBar
            this.parseContentBottomBar(data)
          }
        })
    },
    cellEditingStarted(event, edit) {
      this.gridEditing = true
      if (!edit) return

      // Store row node
      this.currentCellEditNode = this.gridApi.content.getSelectedNodes()[0]
    
      // Store row values
      if (Object.keys(this.currentCellEditValues).length == 0) {
        let node = this.gridApi.content.getSelectedNodes()[0].data
        let keys = Object.keys(node)
        this.currentCellEditValues = {}
        for (let i = 0; i < keys.length; ++i) {
          this.currentCellEditValues[keys[i]] = {'old': node[keys[i]] == 'NULL' ? null : node[keys[i]]}
        }
      }
      // If the cell includes an special character (\n or \t) or the cell == TEXT, ... then open the extended editor
      let columnType = this.contentColumnsType[event.colDef.colId]
      if (['text','mediumtext','longtext'].includes(columnType) || (event.value.toString().match(/\n/g)||[]).length > 0 || (event.value.toString().match(/\t/g)||[]).length > 0) {
        if (this.editDialogEditor != null && this.editDialogEditor.getValue().length > 0) this.editDialogEditor.setValue('')
        else this.editDialogOpen(event.column.colId + ': ' + columnType.toUpperCase(), event.value)
      }
    },
    cellEditingStopped(event, edit) {
      if (!edit || this.editDialog) return

      // Store new value
      if (event.value == 'NULL') this.currentCellEditNode.setDataValue(event.colDef.field, null)
      if (this.currentCellEditMode == 'edit') this.currentCellEditValues[event.colDef.field]['new'] = event.value == 'NULL' ? null : event.value
    },
    cellEditingSubmit(mode, node, values) {
      if (Object.keys(values).length == 0) return

      // Clean vars
      this.currentCellEditMode = 'edit'
      this.currentCellEditNode = {}
      this.currentCellEditValues = {}

      // Compute queries
      var query = ''
      var valuesToUpdate = []
      // NEW
      if (mode == 'new') {
        let keys = Object.keys(node.data)
        for (let i = 0; i < keys.length; ++i) {
          if (node.data[keys[i]] == null) valuesToUpdate.push('NULL')
          else valuesToUpdate.push(JSON.stringify(node.data[keys[i]]))
        }
        query = "INSERT INTO " + this.treeviewSelected['name'] + ' (' + keys.join() + ") VALUES (" + valuesToUpdate.join() + ");"
      }
      // EDIT
      else if (mode == 'edit') {
        let keys = Object.keys(values)
        for (let i = 0; i < keys.length; ++i) {
          if (values[keys[i]]['old'] != values[keys[i]]['new']) {
            if (values[keys[i]]['new'] !== undefined) {
              if (values[keys[i]]['new'] == null) valuesToUpdate.push(keys[i] + " = NULL")
              else valuesToUpdate.push(keys[i] + " = " + JSON.stringify(values[keys[i]]['new']))
            }
          }
        }
        let where = []
        if (this.contentPks.length == 0) {
          for (let i = 0; i < keys.length; ++i) {
            if (values[keys[i]]['old'] == null) where.push(keys[i] + ' IS NULL')
            else where.push(keys[i] + " = " + JSON.stringify(values[keys[i]]['old']))
          }
          query = "UPDATE " + this.treeviewSelected['name'] + " SET " + valuesToUpdate.join(', ') + " WHERE " + where.join(' AND ') + ' LIMIT 1;'
        }
        else {
          for (let i = 0; i < this.contentPks.length; ++i) where.push(this.contentPks[i] + " = " + JSON.stringify(values[this.contentPks[i]]['old']))
          query = "UPDATE " + this.treeviewSelected['name'] + " SET " + valuesToUpdate.join(', ') + " WHERE " + where.join(' AND ') + ';'
        }
      }
      if (mode == 'new' || (mode == 'edit' && valuesToUpdate.length > 0)) {
        this.gridApi.content.showLoadingOverlay()
        // Execute Query
        const payload = {
          server: this.server.id,
          database: this.database,
          queries: [query]
        }
        axios.post('/client/execute', payload)
          .then((response) => {
            this.gridApi.content.hideOverlay()
            let data = JSON.parse(response.data.data)
            // Build BottomBar
            this.parseContentBottomBar(data)
            // Check AUTO_INCREMENTs
            if (data[0].query.startsWith('INSERT')) node.setDataValue(this.contentPks[0], data[0].lastRowId)
          })
          .catch((error) => {
            this.gridApi.content.hideOverlay()
            if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            else {
              // Show error
              let data = JSON.parse(error.response.data.data)
              let dialogOptions = {
                'mode': 'cellEditingError',
                'title': 'Unable to write row',
                'text': data[0]['error'],
                'button1': 'Edit row',
                'button2': 'Discard changes'
              }
              this.showDialog(dialogOptions)
              // Build BottomBar
              this.parseContentBottomBar(data)
              // Restore vars
              this.currentCellEditMode = mode
              this.currentCellEditNode = node
              this.currentCellEditValues = values
            }
          })
      }
    },
    parseContentBottomBar(data) {     
      var elapsed = null
      if (data[data.length-1]['time'] !== undefined) {
        elapsed = 0
        for (let i = 0; i < data.length; ++i) {
          elapsed += parseFloat(data[i]['time'])
        }
        elapsed /= data.length
      }
      this.bottomBarContent['status'] = data[0]['error'] === undefined ? 'success' : 'failure'
      this.bottomBarContent['text'] = data[0]['query']
      this.bottomBarContent['info'] = this.gridApi.content.getDisplayedRowCount() + ' records'
      if (elapsed != null) this.bottomBarContent['info'] += ' | ' + elapsed.toString() + 's elapsed'
    },
    cellEditingDiscard() {
      // Close Dialog
      this.dialog = false

      // Clean vars
      this.currentCellEditMode = 'edit'
      this.currentCellEditNode = {}
      this.currentCellEditValues = {}

      // Get the table data
      this.filterClick()
    },
    cellEditingEdit() {
      // Close Dialog
      this.dialog = false

      // Edit Row
      setTimeout(() => {
        let focused = this.gridApi.content.getFocusedCell()
        this.currentCellEditNode.setSelected(true)
        this.gridApi.content.setFocusedCell(focused.rowIndex, focused.column.colId)
        this.gridApi.content.startEditingCell({
          rowIndex: focused.rowIndex,
          colKey: focused.column.colId
        });
      }, 100);
    },
    filterClick() {
      // Build query condition
      var condition = ''
      if (this.contentSearchFilter == 'BETWEEN') {
        if (this.contentSearchFilterText.length != 0 && this.contentSearchFilterText2.length != 0) condition = ' WHERE ' + this.contentSearchColumn + " BETWEEN '" + this.contentSearchFilterText + "' AND '" + this.contentSearchFilterText2 + "'"
      }
      else if (['IS NULL','IS NOT NULL'].includes(this.contentSearchFilter)) {
        condition = ' WHERE ' + this.contentSearchColumn + ' ' + this.contentSearchFilter
      }
      else if (['IN','NOT IN'].includes(this.contentSearchFilter) && this.contentSearchFilterText.length != 0) {
        condition = ' WHERE ' + this.contentSearchColumn + ' ' + this.contentSearchFilter + " ("
        let elements = this.contentSearchFilterText.split(',')
        for (let i = 0; i < elements.length; ++i) condition += "'" + elements[i] + "',"
        condition = condition.substring(0, condition.length - 1) + ")"
      }
      else if (this.contentSearchFilterText.length != 0) condition = ' WHERE ' + this.contentSearchColumn + ' ' + this.contentSearchFilter + " '" + this.contentSearchFilterText + "'"
      // Show overlay
      this.gridApi.content.showLoadingOverlay()
      // Build payload
      const payload = {
        server: this.server.id,
        database: this.database,
        table: this.treeviewSelected['name'],
        queries: ['SELECT * FROM ' + this.treeviewSelected['name'] + condition + ' LIMIT 1000;' ]
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          this.parseContentExecution(JSON.parse(response.data.data))
        })
        .catch((error) => {
          this.gridApi.content.hideOverlay()
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    editDialogSubmit() {
      this.editDialog = false
      let nodes = this.gridApi.content.getSelectedNodes()
      for (let i = 0; i < nodes.length; ++i) nodes[i].setSelected(false)
      let focusedCell = this.gridApi.content.getFocusedCell()
      let currentNode = this.gridApi.content.getDisplayedRowAtIndex(focusedCell.rowIndex)
      currentNode.setSelected(true)
      currentNode.setDataValue(focusedCell.column.colId, this.editDialogEditor.getValue())
      setTimeout(() => {
        this.gridApi.content.startEditingCell({
          rowIndex: focusedCell.rowIndex,
          colKey: focusedCell.column.colId
        })
      }, 100)
    },
    editDialogCancel() {
      this.editDialog = false
      this.editDialogEditor.setValue('')
    },
    showDialog(options) {
      this.dialogMode = options.mode
      this.dialogTitle = options.title
      this.dialogText = options.text
      this.dialogButtonText1 = options.button1
      this.dialogButtonText2 = options.button2
      this.dialog = true
    },
    dialogSubmit() {
      if (this.dialogMode == 'cellEditingError') this.cellEditingEdit()
      else if (this.dialogMode == 'removeRowConfirm') this.dialog = false
      else if (this.dialogMode == 'info') this.dialog = false
      else if (this.dialogMode == 'export') this.exportRowsSubmit()
    },
    dialogCancel() {
      if (this.dialogMode == 'cellEditingError') this.cellEditingDiscard()
      else if (this.dialogMode == 'removeRowConfirm') this.removeRowSubmit()
      else if (this.dialogMode == 'info') this.dialog = false
      else if (this.dialogMode == 'export') this.dialog = false
    },
    exportRows() {
      // Show confirmation dialog
      this.dialogSelect = 'Meteor'
      var dialogOptions = {
        'mode': 'export',
        'title': 'Export Rows',
        'text': '',
        'button1': 'Export',
        'button2': 'Cancel'
      }
      this.showDialog(dialogOptions)
    },
    exportRowsSubmit() {
      var columns = []
      var rows = []

      // Build Columns
      let displayedColumns = this.columnApi.content.getAllDisplayedColumns()
      for (var i = 0; i < displayedColumns.length; ++i) columns.push(displayedColumns[i]['colId']);

      // Build Rows
      if (['Meteor','JSON','CSV'].includes(this.dialogSelect)) {
        this.gridApi.content.forEachNode(function(rowNode) {
          rows.push(rowNode.data)
        })
      }

      if (this.dialogSelect == 'Meteor') {
        let exportData = 'var DATA = ' + JSON.stringify(rows) + ';\n' + 'var COLUMNS = ' + JSON.stringify(columns) + ';'
        this.download('export.js', exportData)
      }
      else if (this.dialogSelect == 'JSON') {
        let exportData = JSON.stringify(rows)
        this.download('export.json', exportData)
      }
      else if (this.dialogSelect == 'CSV') {
        let replacer = (key, value) => value === null ? '' : value // specify how you want to handle null values here
        let header = Object.keys(rows[0])
        let exportData = rows.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','))
        exportData.unshift(header.join(','))
        exportData = exportData.join('\r\n')
        this.download('export.csv', exportData)
      }
      else if (this.dialogSelect == 'SQL') {
        let exportData = ''
        this.gridApi.content.forEachNode(rowNode => {
          let data = []
          for (let i = 0; i < columns.length; ++i) {
            if (rowNode.data[columns[i]] == null) data.push('NULL')
            else data.push(JSON.stringify(rowNode.data[columns[i]]))
          }
          exportData += "INSERT INTO " + this.treeviewSelected['name'] + ' (' + columns.join() + ") VALUES (" + data.join() + "),\n"
        })
        exportData = exportData.slice(0, -2) + ';'
        this.download('export.sql', exportData)
      }
    },
    download(filename, text) {
      var element = document.createElement('a')
      element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text))
      element.setAttribute('download', filename)
      element.style.display = 'none'
      document.body.appendChild(element)
      element.click()
      document.body.removeChild(element)
    },
  },
}
</script>