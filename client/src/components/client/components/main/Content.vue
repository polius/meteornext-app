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
              <v-select v-model="contentSearchFilter" :items="filterItems" dense solo hide-details height="35px" style="padding-top:5px; padding-left:5px;"></v-select>
            </v-col>
            <v-col v-if="!['BETWEEN','NOT BETWEEN'].includes(contentSearchFilter)">
              <v-text-field @keyup.enter="filterClick" :disabled="['IS NULL','IS NOT NULL'].includes(contentSearchFilter)" v-model="contentSearchFilterText" solo dense hide-details prepend-inner-icon="search" height="35px" style="padding-top:5px; padding-left:5px;"></v-text-field>
            </v-col>
            <v-col v-if="['BETWEEN','NOT BETWEEN'].includes(contentSearchFilter)">
              <v-text-field v-model="contentSearchFilterText" @keyup.enter="filterClick" solo dense hide-details prepend-inner-icon="search" height="35px" style="padding-top:5px; padding-left:5px;"></v-text-field>
            </v-col>
            <v-col v-if="['BETWEEN','NOT BETWEEN'].includes(contentSearchFilter)" sm="auto">
              <div class="body-2" style="margin-top:13px; padding-left:10px; padding-right:5px;">AND</div>
            </v-col>
            <v-col v-if="['BETWEEN','NOT BETWEEN'].includes(contentSearchFilter)">
              <v-text-field v-model="contentSearchFilterText2" @keyup.enter="filterClick" solo dense hide-details prepend-inner-icon="search" height="35px" style="padding-top:5px; padding-left:5px;"></v-text-field>
            </v-col>
            <v-col sm="auto" justify="end">
              <v-btn :loading="contentExecuting" @click="filterClick" style="margin-top:4px; margin-left:6px; margin-right:5px;">Filter</v-btn>
            </v-col>
          </v-row>
        </div>
        <ag-grid-vue ref="agGridContent" suppressDragLeaveHidesColumns suppressFieldDotNotation suppressContextMenu preventDefaultOnContextMenu oncontextmenu="return false" @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" @selection-changed="onSelectionChanged" @row-clicked="onRowClicked" @cell-editing-started="cellEditingStarted" @cell-editing-stopped="cellEditingStopped" @cell-context-menu="onContextMenu" @sort-changed="onSortChanged" style="width:100%; height:calc(100% - 48px);" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" rowDeselection="true" :stopEditingWhenCellsLoseFocus="true" :columnDefs="contentHeaders" :rowData="contentItems"></ag-grid-vue>
        <v-menu v-model="contextMenu" :position-x="contextMenuX" :position-y="contextMenuY" absolute offset-y style="z-index:10">
          <v-list style="padding:0px;">
            <v-list-item-group v-model="contextMenuModel">
              <div v-for="[index, item] of contextMenuItems.entries()" :key="index">
                <v-list-item v-if="item.name != '|'" :disabled="!item.enabled" @click="contextMenuClicked(item.name)">
                  <v-list-item-title>{{ item.name }}</v-list-item-title>
                </v-list-item>
                <v-divider v-else></v-divider>
              </div>
            </v-list-item-group>
          </v-list>
        </v-menu>
      </div>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn :disabled="contentExecuting" @click="filterClick" text small title="Refresh rows" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="addRow" :disabled="contentExecuting || Object.keys(currentCellEditValues).length != 0" text small title="Add row" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="removeRow" :disabled="contentExecuting || !isRowSelected || Object.keys(currentCellEditValues).length != 0" text small title="Remove selected row(s)" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn :disabled="contentItems.length == 0" @click="exportRows" text small title="Export rows" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-arrow-down</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="compressColumns" text small title="Compress columns" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-compress</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="expandColumns" text small title="Expand columns" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-expand</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="previousPage" :disabled="page == 1" text small title="Previous page" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-chevron-left</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="nextPage" :disabled="contentItems.length == 0" text small title="Next page" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-chevron-right</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            <v-icon v-if="bottomBar.content['status']=='executing'" title="Executing" small style="color:rgb(250, 130, 49); padding-bottom:2px; padding-right:7px;">fas fa-spinner</v-icon>
            <v-icon v-else-if="bottomBar.content['status']=='success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:2px; padding-right:7px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBar.content['status']=='failure'" title="Failed" small style="color:#EF5354; padding-bottom:2px; padding-right:7px;">fas fa-times-circle</v-icon>
            <v-icon v-else-if="bottomBar.content['status']=='stopped'" title="Stopped" small style="color:#EF5354; padding-bottom:2px; padding-right:7px;">fas fa-exclamation-circle</v-icon>
            <span :title="bottomBar.content['text']">{{ bottomBar.content['text'] }}</span>
          </div>
        </v-col>
        <v-col v-if="contentExecuting" cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; padding-left:10px; padding-right:5px;">
          <v-btn :loading="loadingStop" @click="stopQuery" small>STOP QUERY</v-btn>
        </v-col>
        <v-col v-else cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBar.content['info'] }}</div>
        </v-col>
      </v-row>
    </div>
    <!-------------------------->
    <!-- DIALOG: EDIT CONTENT -->
    <!-------------------------->
    <v-dialog v-model="editDialog" persistent max-width="80%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">EDIT VALUE</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <div class="white--text text-body-1">{{ `Column: ${editDialogColumnName} (${editDialogColumnType})` }}</div>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-row no-gutters>
                <v-col cols="auto">
                  <v-select @change="editDialogApplyFormat" v-model="editDialogFormat" :items="editDialogFormatItems" label="Format" outlined dense hide-details></v-select>
                </v-col>
                <v-col v-if="editDialogFormat == 'JSON'" cols="auto" style="margin-left:10px">
                  <v-btn @click="editDialogValidate(true)" hide-details style="margin-top:2px">Validate</v-btn>
                </v-col>
                <v-col v-if="editDialogFormat == 'JSON'" cols="auto" style="margin-left:10px">
                  <v-btn @click="editDialogParse" hide-details style="margin-top:2px">Parse</v-btn>
                </v-col>
                <v-col cols="auto" style="margin-left:20px">
                  <v-checkbox @change="editDialogWrapChange" v-model="editDialogWrap" label="Wrap text" hide-details style="margin-top:5px"></v-checkbox>
                </v-col>
              </v-row>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:10px; margin-bottom:15px">
                  <div style="margin-left:auto; margin-right:auto; height:65vh; width:100%">
                    <div id="editDialogEditor" style="height:100%;"></div>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px">
                      <v-btn @click="editDialogSubmit" color="#00b16a">Confirm</v-btn>
                    </v-col>
                    <v-col>
                      <v-btn @click="editDialogCancel" color="#EF5354">Cancel</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!------------------->
    <!-- DIALOG: BASIC -->
    <!------------------->
    <v-dialog v-model="dialog" :persistent="!(['info','export'].includes(dialogMode))" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; padding-bottom:3px">{{ dialogIcon }}</v-icon>{{ dialogTitle }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn v-if="!(['cellEditingError','cellEditingConfirm'].includes(dialogMode))" :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px">
                  <div v-if="dialogText.length > 0" class="body-1">{{ dialogText }}</div>
                  <div v-if="dialogMode == 'cellEditingConfirm'" style="margin-top:15px">
                    <div id="dialogQueryEditorContent" style="height:256px"></div>
                  </div>
                  <v-select v-if="dialogMode=='export'" filled v-model="dialogSelect" :items="['SQL','CSV','JSON']" label="Format" hide-details></v-select>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col v-if="dialogSubmitText.length > 0" cols="auto" style="margin-right:5px">
                      <v-btn :loading="loading" @click="dialogSubmit" :color="dialogSubmitText == 'Close' ? 'primary' : '#00b16a'">{{ dialogSubmitText }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogCancelText.length > 0">
                      <v-btn :disabled="loading" @click="dialogCancel" color="#EF5354">{{ dialogCancelText }}</v-btn>
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

<style scoped>
::v-deep .v-list-item__title {
  font-size: 0.9rem;
}
::v-deep .v-list-item__content {
  padding:0px;
}
::v-deep .v-list-item {
  min-height:40px;
}
</style>

<script>
var JSON2 = require('json-bigint')
import axios from 'axios'

import ace from 'ace-builds';
import sqlFormatter from '@sqltools/formatter'

import {AgGridVue} from "ag-grid-vue";
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

export default {
  data() {
    return {
      // Loading
      loading: false,
      loadingStop: false,
      // AG Grid
      isRowSelected: false,
      currentCellEditMode: 'edit', // edit - new
      currentCellEditNode: {},
      currentCellEditValues: {},
      // Pagination
      page: 1,
      // Filter
      filterItems: ['=', '!=', '>', '<', '>=', '<=', 'LIKE', 'NOT LIKE', 'IN', 'NOT IN', 'BETWEEN', 'NOT BETWEEN', 'IS NULL', 'IS NOT NULL'],
      // Dialog - Content Edit
      editDialog: false,
      editDialogColumnName: '',
      editDialogColumnType: '',
      editDialogFormat: 'Text',
      editDialogFormatItems: ['Text','JSON','Python'],
      editDialogWrap: false,
      editDialogValue: '',
      editDialogEditor: null,
      // Dialog - Basic
      dialog: false,
      dialogMode: '',
      dialogIcon: '',
      dialogTitle: '',
      dialogText: '',
      dialogCode: '',
      dialogQueryEditor: null,
      dialogSubmitText: '',
      dialogCancelText: '',
      // Context Menu
      contextMenu: false,
      contextMenuModel: null,
      contextMenuItems: [],
      contextMenuItem: {},
      contextMenuX: 0,
      contextMenuY: 0,
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'currentConn',
      'dialogOpened',
      'connections',
      'settings',
    ], { path: 'client/client' }),
    ...mapFields([
      'index',
      'id',
      'headerTabSelected',
      'contentHeaders',
      'contentItems',
      'sidebarSelected',
      'server',
      'database',
      'contentSearchFilter',
      'contentSearchFilterText',
      'contentSearchFilterText2',
      'contentSearchColumn',
      'contentColumnsName',
      'contentColumnsDefault',
      'contentColumnsType',
      'contentColumnsExtra',
      'contentPks',
      'contentState',
      'contentSortState',
      'bottomBar',
      'contentExecuting',
    ], { path: 'client/connection' }),
    ...mapFields([
      'gridApi',
      'columnApi',
    ], { path: 'client/components' }),
  },
  activated() {
    EventBus.$on('get-content', this.getContent)
  },
  watch: {
    currentConn() {
      if (this.headerTabSelected == 'content') this.$nextTick(() => this.filterClick())
    },
    sidebarSelected: {
      handler: function () {
        if (this.headerTabSelected == 'content') this.cellEditingDiscard()
      },
      deep: true
    },
    headerTabSelected(newValue, oldValue) {
      if (oldValue == 'content') this.cellEditingDiscard()
    },
    dialog: function(val) {
      this.dialogOpened = this.dialog || this.editDialog
      if (val && this.dialogMode == 'cellEditingConfirm') this.initAceEditor()
    },
    editDialog: function() {
      this.dialogOpened = this.dialog || this.editDialog
    },
  },
  methods: {
    initAceEditor() {
      this.$nextTick(() => {
        this.dialogQueryEditor = ace.edit("dialogQueryEditorContent", {
          mode: "ace/mode/mysql",
          theme: "ace/theme/monokai",
          keyboardHandler: "ace/keyboard/vscode",
          fontSize: 14,
          showPrintMargin: false,
          wrap: false,
          indentedSoftWrap: false,
          showLineNumbers: true,
          scrollPastEnd: true,
          readOnly: true,
        })
        this.dialogQueryEditor.container.addEventListener("keydown", (e) => {
          // - Increase Font Size -
          if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
            let size = parseInt(this.dialogQueryEditor.getFontSize(), 10) || 12
            this.dialogQueryEditor.setFontSize(size + 1)
            e.preventDefault()
          }
          // - Decrease Font Size -
          else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
            let size = parseInt(this.dialogQueryEditor.getFontSize(), 10) || 12
            this.dialogQueryEditor.setFontSize(Math.max(size - 1 || 1))
            e.preventDefault()
          }
        }, false);
        this.dialogQueryEditor.setValue(this.dialogCode, -1)
      })
    },
    onGridReady(params) {
      this.gridApi.content = params.api
      this.columnApi.content = params.columnApi
      this.$refs['agGridContent'].$el.addEventListener('click', this.onGridClick)
      this.gridApi.content.showLoadingOverlay()
    },
    onGridClick(event) {
      if (event.target.className == 'ag-center-cols-viewport') {
        this.gridApi.content.deselectAll()
        this.cellEditingConfirm()
      }
    },
    onSelectionChanged() {
      this.isRowSelected = this.gridApi.content.getSelectedNodes().length > 0
    },
    onRowClicked(event) {
      if (Object.keys(this.currentCellEditNode).length != 0 && this.currentCellEditNode.rowIndex != event.rowIndex) {
        this.cellEditingConfirm()
      }
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        let selectedRows = this.gridApi.content.getSelectedRows()
        if (selectedRows.length > 1) {
          // Copy values
          let header = Object.keys(selectedRows[0])
          let value = selectedRows.map(row => header.map(fieldName => row[fieldName] == null ? 'NULL' : row[fieldName]).join('\t')).join('\n')
          this.copyToClipboard(value)
          // Apply effect
          // this.gridApi.content.flashCells({
          //   rowNodes: this.gridApi.content.getSelectedNodes(),
          //   flashDelay: 200,
          //   fadeDelay: 200,
          // })
        }
        else {
          // Copy value
          this.copyToClipboard(e.value).then(() => {
            // Apply effect
            this.gridApi.content.flashCells({
              rowNodes: this.gridApi.content.getSelectedNodes(),
              columns: [this.gridApi.content.getFocusedCell().column.colId],
              flashDelay: 200,
              fadeDelay: 200,
            })
          })
        }
      }
      else if (e.event.key == 'Enter') {
        this.cellEditingConfirm()
      }
      else if (['ArrowUp','ArrowDown'].includes(e.event.key)) {
        let cell = this.gridApi.content.getFocusedCell()
        let row = this.gridApi.content.getDisplayedRowAtIndex(cell.rowIndex)
        let node = this.gridApi.content.getRowNode(row.id)
        this.gridApi.content.deselectAll()
        node.setSelected(true)
      }
      else if (e.event.key == 'a' && (e.event.ctrlKey || e.event.metaKey)) {
        this.gridApi.content.selectAll()
      }
    },
    onSortChanged() {
      this.filterClick()
    },
    onContextMenu(e) {
      if (!this.gridApi.content.getSelectedNodes().some(x => x.id == e.node.id)) this.gridApi.content.deselectAll()
      e.node.setSelected(true)
      this.contextMenuModel = null
      this.contextMenuX = e.event.clientX
      this.contextMenuY = e.event.clientY
      let selectedRows = this.gridApi.content.getSelectedRows().length
      this.contextMenuItems = [
        { name: 'Copy SQL', enabled: true },
        { name: 'Copy CSV', enabled: true },
        { name: 'Copy JSON', enabled: true },
        { name: '|', enabled: true },
        { name: 'Duplicate Row', enabled: selectedRows == 1 },
        { name: selectedRows > 1 ? 'Remove Rows' : 'Remove Row', enabled: true },
        { name: '|', enabled: true },
        { name: 'Select All', enabled: true },
        { name: 'Deselect All', enabled: true },
      ]
      this.contextMenu = true
    },
    contextMenuClicked(item) {
      if (item == 'Copy SQL') this.copySQL()
      else if (item == 'Copy CSV') this.copyCSV()
      else if (item == 'Copy JSON') this.copyJSON()
      else if (item == 'Duplicate Row') this.duplicateRow()
      else if (item.startsWith('Remove Row')) this.removeRow()
      else if (item == 'Select All') this.gridApi.content.selectAll()
      else if (item == 'Deselect All') this.gridApi.content.deselectAll()
    },
    copySQL() {
      var SqlString = require('sqlstring');
      let selectedRows = this.gridApi.content.getSelectedRows()
      let rawQuery = 'INSERT INTO `' + this.sidebarSelected[0]['name'] + '` (' + Object.keys(selectedRows[0]).map(x => '`' + x.trim() + '`').join() + ')\nVALUES\n'
      let values = ''
      let args = []
      for (let row of selectedRows) {
        let rowVal = Object.values(row).map(x => x == null ? null : x.toString())
        args = [...args, ...rowVal];
        values += '(' + '?,'.repeat(rowVal.length).slice(0, -1) + '),\n'
      }
      rawQuery += values.slice(0,-2) + ';'
      let query = SqlString.format(rawQuery, args)
      this.copyToClipboard(query)
    },
    copyCSV() {
      let selectedRows = this.gridApi.content.getSelectedRows()
      let replacer = (key, value) => value === null ? undefined : value
      let header = Object.keys(selectedRows[0])
      let csv = selectedRows.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','))
      csv.unshift(header.join(','))
      csv = csv.join('\r\n')
      this.copyToClipboard(csv)
    },
    copyJSON() {
      let selectedRows = this.gridApi.content.getSelectedRows()
      let json = JSON.stringify(selectedRows)
      this.copyToClipboard(json)
    },
    getContent(force) {
      if (this.contentExecuting) return
      if (!force && this.contentState == (this.database + '|' + this.sidebarSelected[0]['id'])) return
      if (force) { this.contentSearchColumn = ''; this.contentSearchFilter = '='; this.contentSearchFilterText = ''; this.contentSearchFilterText2 = ''; }
      this.contentExecuting = true
      this.contentSortState = []
      this.gridApi.content.showLoadingOverlay()
      const payload = {
        origin: 'content',
        connection: this.id + '-shared',
        server: this.server.id,
        database: this.database,
        table: this.sidebarSelected[0]['name'],
        queries: ['SELECT * FROM `' + this.sidebarSelected[0]['name'] + '` LIMIT 1000;' ]
      }
      this.bottomBar.content = { status: 'executing', text: payload.queries[0], info: '' }
      const server = this.server
      const index = this.index
      const startTime = new Date()
      axios.post('/client/execute', payload)
        .then((response) => {
          const elapsed = (new Date() - startTime) / 1000
          let data = JSON2.parse(response.data.data)
          this.parseContentExecution(data, elapsed)
          // Add execution to history
          const history = { section: 'content', server: server, queries: data, elapsed: elapsed }
          this.$store.dispatch('client/addHistory', history)
          let current = this.connections.find(c => c['index'] == index)
          if (current === undefined) return
          current.contentExecuting = false
        })
        .catch((error) => {
          const elapsed = (new Date() - startTime) / 1000
          let current = this.connections.find(c => c['index'] == index)
          if (current === undefined) return
          current.contentExecuting = false
          this.gridApi.content.hideOverlay()
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            // Show error
            let data = ''
            if ([502,504].includes(error.response.status)) data = [{"query": payload['queries'][0], "database": payload['database'], "error": "The request has been interrupted by the proxy server. If you are using a reverse proxy please increase the timeout value 'proxy_read_timeout' in Nginx or 'ProxyTimeout' in Apache."}]
            else data = JSON2.parse(error.response.data.data)
            error = data.find(x => 'error' in x)['error']
            EventBus.$emit('send-notification', error, '#EF5354')
            // Build bottom bar
            this.parseContentBottomBar(data, elapsed)
            // Add execution to history
            const history = { section: 'content', server: server, queries: data, elapsed: elapsed }
            this.$store.dispatch('client/addHistory', history)
          }
        })
    },
    parseContentExecution(data, elapsed) {
      // Build Data Table
      var headers = []
      var items = data[0]['data']
      // Build Headers
      if (data.length > 0) {
        this.contentColumnsName = data[0]['columns']['name']
        this.contentColumnsDefault = data[0]['columns']['default']
        this.contentColumnsType = data[0]['columns']['type']
        this.contentColumnsExtra = data[0]['columns']['extra']
        this.contentPks = data[0]['pks']
        if (this.contentSearchColumn.length == 0) this.contentSearchColumn = this.contentColumnsName[0].trim()
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
      if (this.contentSortState.length > 0) {
        headers = headers.map(x => (x.colId == this.contentSortState[0].colId ? {...x, sort: this.contentSortState[0].sort} : x))
      }

      // Load table header
      if (data.length > 0) {
        const currentCols = this.gridApi.content.getColumnDefs()
        const newCols = data[0]['columns']['name']
        let match = currentCols.length == newCols.length
        if (match) {
          for (let i = 0; i < currentCols.length; ++i) {
            if (currentCols[i].colId != newCols[i]) {
              match = false
              break
            }
          }
        }
        if (!match) {
          this.gridApi.content.setColumnDefs([])
          this.contentHeaders = headers
        }
      }

      // Build Items
      this.contentItems = items
      this.isRowSelected = false

      // Build BottomBar
      this.parseContentBottomBar(data, elapsed)

      // Store the content state
      this.contentState = (this.database + '|' + this.sidebarSelected[0]['id'])
    },
    resizeTable() {
      let allColumnIds = this.columnApi.content.getColumns().map(v => v.colId)
      this.columnApi.content.autoSizeColumns(allColumnIds)
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
    duplicateRow() {
      // Clean vars
      this.currentCellEditValues = {}
      this.currentCellEditNode = {}
      this.currentCellEditMode = 'new'

      var rowCount = this.gridApi.content.getDisplayedRowCount()
      var nodes = this.gridApi.content.getSelectedNodes()
      for (let i = 0; i < nodes.length; ++i) nodes[i].setSelected(false)

      var newData = {}
      for (let i = 0; i < this.contentColumnsName.length; ++i) {
        newData[this.contentColumnsName[i]] = (this.contentColumnsExtra[i] == 'auto_increment') ? null : nodes[0]['data'][this.contentColumnsName[i]]
      }

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
        'icon': 'fas fa-minus',
        'title': 'DELETE ROWs',
        'text': 'Are you sure you want to delete the selected ' + this.gridApi.content.getSelectedNodes().length + ' rows from this table? This action cannot be undone.',
        'code': '',
        'button1': 'Confirm',
        'button2': 'Cancel'
      }
      this.showDialog(dialogOptions)
    },
    removeRowSubmit() {
      this.contentExecuting = true
      let nodes = this.gridApi.content.getSelectedNodes()
      var queries = []
      if (this.contentPks.length == 0) {
        for (let i = 0; i < nodes.length; ++i) {
          let where = []
          for (let [key, value] of Object.entries(nodes[i].data)) {
            if (value == null) where.push(key + ' IS NULL')
            else {
              let binary = (this.contentColumnsType[key] == 'json') ? 'BINARY ' : ''
              where.push(binary + key + " = " + JSON.stringify(value))
            }
          }
          queries.push('DELETE FROM `' + this.sidebarSelected[0]['name'] + '` WHERE ' + where.join(' AND ') + ' LIMIT 1;')
        }
      }
      else {
        let pks = []
        for (let i = 0; i < nodes.length; ++i) {
          let pk = []
          for (let j = 0; j < this.contentPks.length; ++j) {
            pk.push(this.contentPks[j] + " = '" + nodes[i].data[this.contentPks[j]] + "'")
          }
          pks.push('(' + pk.join(' AND ') + ')')
        }
        queries = ['DELETE FROM `' + this.sidebarSelected[0]['name'] + '` WHERE ' + pks.join(' OR ') + ';']
      }
      // Show overlay
      this.gridApi.content.showLoadingOverlay()
      // Close Dialog
      this.dialog = false
      // Execute Query/ies
      const payload = {
        origin: 'content',
        connection: this.id + '-shared',
        server: this.server.id,
        database: this.database,
        queries: queries
      }
      this.bottomBar.content = { status: 'executing', text: queries[queries.length - 1], info: '' }
      const server = this.server
      const index = this.index
      const startTime = new Date()
      axios.post('/client/execute', payload)
        .then((response) => {
          const elapsed = (new Date() - startTime) / 1000
          // Get Response Data
          let data = JSON2.parse(response.data.data)
          // Remove Frontend Rows
          this.gridApi.content.applyTransaction({ remove: this.gridApi.content.getSelectedRows() })
          // Build BottomBar
          this.parseContentBottomBar(data, elapsed)
          // Mark contentExecuting to false
          let current = this.connections.find(c => c['index'] == index)
          if (current === undefined) return
          current.contentExecuting = false
          // Add execution to history
          const history = { section: 'content', server: server, queries: data, elapsed: elapsed }
          this.$store.dispatch('client/addHistory', history)
        })
        .catch((error) => {
          const elapsed = (new Date() - startTime) / 1000
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            let current = this.connections.find(c => c['index'] == index)
            if (current === undefined) return
            current.contentExecuting = false
            this.gridApi.content.hideOverlay()
            // Show error
            let data = ''
            if ([502,504].includes(error.response.status)) data = [{"query": payload['queries'][0], "database": payload['database'], "error": "The request has been interrupted by the proxy server. If you are using a reverse proxy please increase the timeout value 'proxy_read_timeout' in Nginx or 'ProxyTimeout' in Apache."}]
            else data = JSON2.parse(error.response.data.data)
            let dialogOptions = {
              'mode': 'info',
              'icon': 'fas fa-exclamation-triangle',
              'title': 'ERROR',
              'text': data.find(x => 'error' in x).error,
              'code': '',
              'button1': 'Close',
              'button2': ''
            }
            this.showDialog(dialogOptions)
            // Build BottomBar
            this.parseContentBottomBar(data, elapsed)
            // Add execution to history
            const history = { section: 'content', server: server, queries: data, elapsed: elapsed }
            this.$store.dispatch('client/addHistory', history)
          }
        })
    },
    cellEditingStarted(event) {
      this.$nextTick(() => {
        // Select edited row
        this.gridApi.content.getSelectedNodes().forEach(x => x.setSelected(false))
        event.node.setSelected(true)
        // Check if the user edited a different row
        if (this.currentCellEditMode == 'edit' && this.currentCellEditNode.rowIndex != event.rowIndex && this.cellEditingValuesToUpdate(this.currentCellEditValues)) {
          this.cellEditingConfirm()
          return
        }
        // Store row values
        if (this.currentCellEditNode.rowIndex != event.rowIndex) {
          let node = event.node.data
          let keys = Object.keys(node)
          this.currentCellEditValues = {}
          for (let i = 0; i < keys.length; ++i) {
            this.currentCellEditValues[keys[i]] = {'old': node[keys[i]] == 'NULL' ? null : node[keys[i]]}
          }
        }
        // Store row node
        this.currentCellEditNode = event.node
        // If the cell includes an special character (\n or \t) or the cell == TEXT, ... then open the extended editor
        let columnType = this.contentColumnsType[event.colDef.colId]
        if (['text','mediumtext','longtext','blob','mediumblob','longblob','json'].includes(columnType) || (event.value.toString().match(/\n/g)||[]).length > 0 || (event.value.toString().match(/\t/g)||[]).length > 0) {
          if (this.editDialogEditor != null && this.editDialogEditor.getValue().length > 0) this.editDialogEditor.setValue('')
          else this.editDialogOpen(event.column.colId, columnType.toUpperCase(), event.value)
        }
      })
    },
    cellEditingStopped(event) {
      // Store new value
      if (event.value == 'NULL') this.currentCellEditNode.setDataValue(event.colDef.field, null)
      if (this.currentCellEditMode == 'edit' && this.currentCellEditValues[event.colDef.field] !== undefined) {
        if (this.currentCellEditNode.rowIndex == event.rowIndex) {
          this.currentCellEditValues[event.colDef.field]['new'] = event.value == 'NULL' ? null : event.value
        }
      }
    },
    cellEditingConfirm() {
      this.cellEditingSubmit(this.currentCellEditMode, this.currentCellEditNode, this.currentCellEditValues, false)
    },
    cellEditingConfirmSubmit() {
      this.cellEditingSubmit(this.currentCellEditMode, this.currentCellEditNode, this.currentCellEditValues, true)
    },
    cellEditingValuesToUpdate(values) {
      if (this.currentCellEditMode == 'new') return true
      else if (this.currentCellEditMode == 'edit') {
        let keys = Object.keys(values)
        for (let i = 0; i < keys.length; ++i) {
          if (values[keys[i]]['old'] != values[keys[i]]['new']) {
            if (values[keys[i]]['new'] !== undefined) return true
          }
        }
      }
      return false
    },
    cellEditingSubmit(mode, node, values, confirm=false) {
      if (Object.keys(values).length == 0) return
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
        query = "INSERT INTO `" + this.sidebarSelected[0]['name'] + '` (' + keys.map(x => `\`${x}\``).join(',') + ") VALUES (" + valuesToUpdate.join() + ");"
      }
      // EDIT
      else if (mode == 'edit') {
        let keys = Object.keys(values)
        for (let i = 0; i < keys.length; ++i) {
          if (values[keys[i]]['old'] != values[keys[i]]['new']) {
            if (values[keys[i]]['new'] !== undefined) {
              if (values[keys[i]]['new'] == null) valuesToUpdate.push('`' + keys[i] + "` = NULL")
              else valuesToUpdate.push('`' + keys[i] + "` = " + JSON.stringify(values[keys[i]]['new']))
            }
          }
        }
        let where = []
        if (this.contentPks.length == 0) {
          for (let i = 0; i < keys.length; ++i) {
            if (values[keys[i]]['old'] == null) where.push('`' + keys[i] + '` IS NULL')
            else {
              let binary = (this.contentColumnsType[keys[i]] == 'json') ? 'BINARY ' : ''
              where.push(binary + '`' + keys[i] + "` = " + JSON.stringify(values[keys[i]]['old']))
            }
          }
          query = "UPDATE `" + this.sidebarSelected[0]['name'] + "` SET " + valuesToUpdate.join(', ') + " WHERE " + where.join(' AND ') + ' LIMIT 1;'
        }
        else {
          for (let i = 0; i < this.contentPks.length; ++i) where.push('`' + this.contentPks[i] + "` = " + JSON.stringify(values[this.contentPks[i]]['old']))
          query = "UPDATE `" + this.sidebarSelected[0]['name'] + "` SET " + valuesToUpdate.join(', ') + " WHERE " + where.join(' AND ') + ';'
        }
      }
      if (mode == 'new' || (mode == 'edit' && valuesToUpdate.length > 0)) {
        // Check Secure Mode
        if (!confirm && (!Object.keys(this.settings).includes('secure_mode') || parseInt(this.settings['secure_mode']))) {
          let beautified = sqlFormatter.format(query, { reservedWordCase: 'upper', linesBetweenQueries: 2 })
          var dialogOptions = {
            'mode': 'cellEditingConfirm',
            'icon': 'fas fa-exclamation-triangle',
            'title': 'CONFIRMATION',
            'text': 'Do you want to confirm these changes?',
            'code': beautified,
            'button1': 'Confirm',
            'button2': 'Cancel'
          }
          this.showDialog(dialogOptions)
          return
        }
        this.contentExecuting = true
        this.gridApi.content.showLoadingOverlay()
        // Execute Query
        const payload = {
          origin: 'content',
          connection: this.id + '-shared',
          server: this.server.id,
          database: this.database,
          queries: [query]
        }
        this.bottomBar.content = { status: 'executing', text: query, info: '' }
        const server = this.server
        const index = this.index
        const startTime = new Date()
        axios.post('/client/execute', payload)
          .then((response) => {
            const elapsed = (new Date() - startTime) / 1000
            this.gridApi.content.hideOverlay()
            let data = JSON2.parse(response.data.data)
            // Build BottomBar
            this.parseContentBottomBar(data, elapsed)
            // Check AUTO_INCREMENTs
            if (data[0].query.startsWith('INSERT') && this.contentPks.length > 0 && data[0].lastRowId != 0) {
              node.setDataValue(this.contentPks[0], data[0].lastRowId)
            }
            // Mark contentExecuting to false
            let current = this.connections.find(c => c['index'] == index)
            if (current === undefined) return
            current.contentExecuting = false
            // Add execution to history
            const history = { section: 'content', server: server, queries: data, elapsed: elapsed }
            this.$store.dispatch('client/addHistory', history)
            // Clean vars
            this.currentCellEditMode = 'edit'
            this.currentCellEditNode = {}
            this.currentCellEditValues = {}
          })
          .catch((error) => {
            const elapsed = (new Date() - startTime) / 1000
            if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else {
              // Mark contentExecuting to false
              let current = this.connections.find(c => c['index'] == index)
              if (current === undefined) return
              current.contentExecuting = false
              this.gridApi.content.hideOverlay()
              // Show error
              let data = ''
              if ([502,504].includes(error.response.status)) data = [{"query": payload['queries'][0], "database": payload['database'], "error": "The request has been interrupted by the proxy server. If you are using a reverse proxy please increase the timeout value 'proxy_read_timeout' in Nginx or 'ProxyTimeout' in Apache."}]
              else data = JSON2.parse(error.response.data.data)
              let dialogOptions = {
                'mode': 'cellEditingError',
                'icon': 'fas fa-exclamation-triangle',
                'title': 'ERROR',
                'text': data.find(x => 'error' in x).error,
                'code': '',
                'button1': 'Edit row',
                'button2': 'Discard changes'
              }
              this.showDialog(dialogOptions)
              // Build BottomBar
              this.parseContentBottomBar(data, elapsed)
              // Import vars
              this.currentCellEditMode = mode
              this.currentCellEditNode = node
              this.currentCellEditValues = values
              // Add execution to history
              const history = { section: 'content', server: server, queries: data, elapsed: elapsed }
              this.$store.dispatch('client/addHistory', history)
            }
          })
      }
      else {
        // Clean vars
        this.currentCellEditMode = 'edit'
        this.currentCellEditNode = {}
        this.currentCellEditValues = {}
      }
    },
    parseContentBottomBar(data, elapsed) {
      this.bottomBar.content['status'] = data[0]['error'] === undefined ? 'success' : 'failure'
      this.bottomBar.content['text'] = data[0]['query']
      this.bottomBar.content['info'] = data[0]['rowCount'] !== undefined ? data[0]['rowCount'] + ' records' : ' 0 records'
      this.bottomBar.content['info'] += ' | ' + elapsed.toFixed(3).toString() + 's elapsed'
    },
    cellEditingDiscard() {
      // Close Dialog
      this.dialog = false
      // Import Values
      const diff = Object.keys(this.currentCellEditValues).filter(x => 'new' in this.currentCellEditValues[x]).reduce((acc,val) => { acc[val] = this.currentCellEditValues[val]['old']; return acc; },{})
      if (Object.keys(diff).length == 0 && Object.keys(this.currentCellEditNode).length > 0) this.gridApi.content.applyTransaction({ remove: [this.currentCellEditNode.data] });
      for (const [k,v] of Object.entries(diff)) this.currentCellEditNode.setDataValue(k, v)
      // Clean vars
      this.currentCellEditMode = 'edit'
      this.currentCellEditNode = {}
      this.currentCellEditValues = {}
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
      if (this.contentExecuting) return
      this.contentExecuting = true
      // Check if column name is a JSON
      let binary = (this.contentColumnsType[this.contentSearchColumn] == 'json') ? ' BINARY ' : ''
      // Build query condition
      var condition = ''
      if (['BETWEEN','NOT BETWEEN'].includes(this.contentSearchFilter)) {
        if (this.contentSearchFilterText.length != 0 && this.contentSearchFilterText2.length != 0) condition = ' WHERE' + binary + '`' + this.contentSearchColumn + '` ' + this.contentSearchFilter + " '" + this.contentSearchFilterText + "' AND '" + this.contentSearchFilterText2 + "'"
      }
      else if (['IS NULL','IS NOT NULL'].includes(this.contentSearchFilter)) {
        condition = ' WHERE `' + this.contentSearchColumn + '` ' + this.contentSearchFilter
      }
      else if (['IN','NOT IN'].includes(this.contentSearchFilter) && this.contentSearchFilterText.length != 0) {
        condition = ' WHERE' + binary + '`' + this.contentSearchColumn + '` ' + this.contentSearchFilter + " ("
        let elements = this.contentSearchFilterText.split(',')
        for (let i = 0; i < elements.length; ++i) condition += "'" + elements[i] + "',"
        condition = condition.substring(0, condition.length - 1) + ")"
      }
      else if (this.contentSearchFilterText.length != 0) condition = ' WHERE' + binary + '`' + this.contentSearchColumn + '` ' + this.contentSearchFilter + " '" + this.contentSearchFilterText + "'"
      // Build pagination
      var pagination = (this.page == 1) ? ' LIMIT 1000' : ' LIMIT 1000 OFFSET ' + (this.page-1) * 1000
      // Build sort
      this.contentSortState = this.columnApi.content.getColumnState().filter(x => x.sort != null).map(x => ({ colId: x.colId, sort: x.sort }))
      const sort = this.contentSortState.length == 0 ? '' : ' ORDER BY `' + this.contentSortState[0].colId + '` ' + this.contentSortState[0].sort.toUpperCase()
      // Show overlay
      this.gridApi.content.showLoadingOverlay()
      // Build payload
      const payload = {
        origin: 'content',
        connection: this.id + '-shared',
        server: this.server.id,
        database: this.database,
        table: this.sidebarSelected[0]['name'],
        queries: ['SELECT * FROM `' + this.sidebarSelected[0]['name'] + '`' + condition + sort + pagination + ';' ]
      }
      this.bottomBar.content = { status: 'executing', text: payload.queries[0], info: '' }
      const server = this.server
      const index = this.index
      const startTime = new Date()
      axios.post('/client/execute', payload)
        .then((response) => {
          const elapsed = (new Date() - startTime) / 1000
          let data = JSON2.parse(response.data.data)
          // Add execution to history
          const history = { section: 'content', server: server, queries: data, elapsed: elapsed }
          this.$store.dispatch('client/addHistory', history)
          let current = this.connections.find(c => c['index'] == index)
          if (current === undefined) return
          current.contentExecuting = false
          this.parseContentExecution(data, elapsed)
        })
        .catch((error) => {
          const elapsed = (new Date() - startTime) / 1000
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            let current = this.connections.find(c => c['index'] == index)
            if (current === undefined) return
            current.contentExecuting = false
            this.gridApi.content.hideOverlay()
            // Show error
            let data = ''
            if ([502,504].includes(error.response.status)) data = [{"query": payload['queries'][0], "database": payload['database'], "error": "The request has been interrupted by the proxy server. If you are using a reverse proxy please increase the timeout value 'proxy_read_timeout' in Nginx or 'ProxyTimeout' in Apache."}]
            else data = JSON2.parse(error.response.data.data)
            EventBus.$emit('send-notification', data[0]['error'], '#EF5354')
            // Build bottom bar
            this.parseContentBottomBar(data, elapsed)
            // Add execution to history
            const history = { section: 'content', server: server, queries: data, elapsed: elapsed }
            this.$store.dispatch('client/addHistory', history)
          }
        })
    },
    previousPage() {
      this.page -= 1
      this.filterClick()
    },
    nextPage() {
      this.page += 1
      this.filterClick()
    },
    showDialog(options) {
      this.dialogMode = options.mode
      this.dialogIcon = options.icon
      this.dialogTitle = options.title
      this.dialogText = options.text
      this.dialogCode = options.code
      this.dialogSubmitText = options.button1
      this.dialogCancelText = options.button2
      this.dialog = true
    },
    dialogSubmit() {
      if (this.dialogMode == 'cellEditingError') this.cellEditingEdit()
      else if (this.dialogMode == 'removeRowConfirm') this.removeRowSubmit()
      else if (this.dialogMode == 'info') { this.dialog = false; this.$nextTick(() => this.editDialogEditor.focus()) }
      else if (this.dialogMode == 'export') this.exportRowsSubmit()
      else if (this.dialogMode == 'cellEditingConfirm') { this.dialog = false; this.cellEditingConfirmSubmit() }
    },
    dialogCancel() {
      if (['cellEditingError','cellEditingConfirm'].includes(this.dialogMode)) this.cellEditingDiscard()
      this.dialog = false
    },
    editDialogOpen(columnName, columnType, text) {
      text = (this.currentCellEditMode == 'new') ? '' : text
      this.editDialogColumnName = columnName
      this.editDialogColumnType = columnType
      this.editDialog = true
      if (this.editDialogEditor == null) {
        this.$nextTick(() => {
          this.editDialogEditor = ace.edit("editDialogEditor", {
            mode: "ace/mode/text",
            theme: "ace/theme/monokai",
            keyboardHandler: "ace/keyboard/vscode",
            fontSize: 14,
            showPrintMargin: false,
            wrap: false,
            indentedSoftWrap: false,
            showLineNumbers: true,
            scrollPastEnd: true
          })
          this.editDialogEditor.container.addEventListener("keydown", (e) => {
            // - Increase Font Size -
            if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
              let size = parseInt(this.editDialogEditor.getFontSize(), 10) || 12
              this.editDialogEditor.setFontSize(size + 1)
              e.preventDefault()
            }
            // - Decrease Font Size -
            else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
              let size = parseInt(this.editDialogEditor.getFontSize(), 10) || 12
              this.editDialogEditor.setFontSize(Math.max(size - 1 || 1))
              e.preventDefault()
            }
          }, false);
        })
      }
      this.$nextTick(() => {
        this.editDialogEditor.setValue(text, -1)
        this.editDialogDetectFormat(columnType, text)
        setTimeout(() => this.editDialogEditor.focus(), 0)
      })
    },
    editDialogWrapChange(val) {
      this.editDialogEditor.getSession().setUseWrapMode(val)
    },
    editDialogDetectFormat(columnType, text) {
      // Detect JSON and parse it
      try {
        let value = (columnType != 'JSON' || text.length != 0) ? JSON2.stringify(JSON2.parse(text), null, '\t') : text
        this.editDialogEditor.session.setMode("ace/mode/json")
        this.editDialogEditor.session.setTabSize(2)
        this.editDialogEditor.setValue(value, 1)
        this.editDialogFormat = 'JSON'
      } catch { 
        this.editDialogFormat = 'Text'
        this.editDialogEditor.session.setTabSize(4)
        this.editDialogEditor.session.setMode("ace/mode/text")
      }
    },
    editDialogApplyFormat(val) {
      this.editDialogEditor.session.setMode("ace/mode/" + val.toLowerCase())
      if (val == 'JSON') {
        try {
          let parsed = JSON2.parse(this.editDialogEditor.getValue())
          this.editDialogEditor.session.setTabSize(2)
          this.editDialogEditor.setValue(JSON2.stringify(parsed, null, '\t'), 1)
        } catch { 1==1 }
      }
      else {
        try {
          let parsed = JSON2.parse(this.editDialogEditor.getValue())
          this.editDialogEditor.session.setTabSize(4)
          this.editDialogEditor.setValue(JSON2.stringify(parsed), 1)
        } catch { 1==1 }
      }
    },
    editDialogValidate(notification) {
      try {
        JSON.parse(this.editDialogEditor.getValue())
        if (notification) EventBus.$emit('send-notification', 'JSON Validated!', '#00b16a', 2)
        return true
      } catch (error) {
        var dialogOptions = {
          'mode': 'info',
          'icon': 'fas fa-exclamation-triangle',
          'title': 'JSON NOT VALIDATED',
          'text': error.toString(),
          'code': '',
          'button1': 'Close',
          'button2': ''
        }
        this.showDialog(dialogOptions)
        return false
      }
    },
    editDialogParse() {
      try {
        let parsed = JSON2.parse(this.editDialogEditor.getValue())
        this.editDialogEditor.setValue(JSON2.stringify(parsed, null, '\t'), 1)
      } catch (error) {
        var dialogOptions = {
          'mode': 'info',
          'icon': 'fas fa-exclamation-triangle',
          'title': 'JSON NOT VALIDATED',
          'text': error.toString(),
          'code': '',
          'button1': 'Close',
          'button2': ''
        }
        this.showDialog(dialogOptions)
      }
    },
    editDialogSubmit() {
      if (this.editDialogFormat == 'JSON' && !this.editDialogValidate(false)) return
      let value = this.editDialogEditor.getValue()
      try { value = JSON2.stringify(JSON2.parse(value)) } catch { 1==1 }
      this.editDialog = false
      let nodes = this.gridApi.content.getSelectedNodes()
      for (let i = 0; i < nodes.length; ++i) nodes[i].setSelected(false)
      let focusedCell = this.gridApi.content.getFocusedCell()
      let currentNode = this.gridApi.content.getDisplayedRowAtIndex(focusedCell.rowIndex)
      currentNode.setSelected(true)
      currentNode.setDataValue(focusedCell.column.colId, value)
      this.$nextTick(() => {
        this.gridApi.content.startEditingCell({
          rowIndex: focusedCell.rowIndex,
          colKey: focusedCell.column.colId
        })
      })
    },
    editDialogCancel() {
      if (this.currentCellEditMode == 'new') this.cellEditingDiscard()
      this.editDialog = false
      this.editDialogEditor.setValue('')
    },
    exportRows() {
      // Show confirmation dialog
      this.dialogSelect = 'SQL'
      var dialogOptions = {
        'mode': 'export',
        'icon': 'fas fa-arrow-down',
        'title': 'EXPORT ROWs',
        'text': '',
        'code': '',
        'button1': 'Export',
        'button2': 'Cancel'
      }
      this.showDialog(dialogOptions)
    },
    exportRowsSubmit() {
      this.loading = true
      const name = this.sidebarSelected[0]['name']
      if (this.dialogSelect == 'JSON') {
        let exportData = JSON.stringify(this.contentItems)
        this.download(name + '.json', exportData)
      }
      else if (this.dialogSelect == 'CSV') {
        let replacer = (key, value) => value === null ? undefined : value
        let header = Object.keys(this.contentItems[0])
        let exportData = this.contentItems.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','))
        exportData.unshift(header.join(','))
        exportData = exportData.join('\r\n')
        this.download(name + '.csv', exportData)
      }
      else if (this.dialogSelect == 'SQL') {
        var SqlString = require('sqlstring');
        let rawQuery = 'INSERT INTO `' + this.sidebarSelected[0]['name'] + '` (' + this.contentHeaders.map(x => '`' + x.headerName.trim() + '`').join() + ')\nVALUES\n'
        let values = ''
        let args = []
        for (let row of this.contentItems) {
          let rowVal = Object.values(row).map(x => x == null ? null : x.toString())
          args = [...args, ...rowVal];
          values += '(' + '?,'.repeat(rowVal.length).slice(0, -1) + '),\n'
        }
        rawQuery += values.slice(0,-2) + ';'
        let exportData = SqlString.format(rawQuery, args)
        this.download(name + '.sql', exportData)
      }
      this.loading = false
    },
    compressColumns() {
      this.resizeTable()
    },
    expandColumns() {
      this.gridApi.content.sizeColumnsToFit()
    },
    download(filename, text) {
      const a = document.createElement('a')
      a.href = URL.createObjectURL(new Blob([text]))
      a.setAttribute('download', filename)
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    },
    stopQuery() {
      if (this.loadingStop) return
      this.loadingStop = true
      const payload = { connection: this.id + '-shared' }
      axios.post('/client/stop', payload)
      .then(() => {
        this.bottomBar.content['status'] = 'stopped'
      })
      .catch((error) => {
        if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else EventBus.$emit('send-notification', "An error occurred stopping the query. Please try again.", '#EF5354')
      })
      .finally(() => this.loadingStop = false)
    },
    copyToClipboard(textToCopy) {
      if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(textToCopy)
      else {
        let textArea = document.createElement("textarea")
        textArea.value = textToCopy
        textArea.style.position = "absolute"
        textArea.style.opacity = 0
        document.body.appendChild(textArea)
        textArea.select()
        return new Promise((res, rej) => {
          document.execCommand('copy') ? res() : rej()
          textArea.remove()
        })
      }
    },
  },
}
</script>