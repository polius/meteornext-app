<template>
  <div>
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
    <!------------->
    <!-- DIALOGS -->
    <!------------->
    <v-dialog v-model="editDialog" persistent max-width="80%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">{{ editDialogTitle }}</div>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:10px; margin-bottom:15px;">
                  <div style="margin-left:auto; margin-right:auto; height:60vh; width:100%">
                    <div id="editDialogEditor" style="float:left;"></div>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn @click="editDialogSubmit" color="primary">Save</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn @click="editDialogCancel" outlined color="#e74d3c">Cancel</v-btn>
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
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
        'clientHeaders',
        'clientItems',
        'editDialog',
        'editDialogTitle',
        'treeviewSelected',
        'structureHeaders',
        'contentTableSelected',
        'gridApi',
        'columnApi',
        'currentCellEditMode',
        'currentCellEditNode',
        'currentCellEditValues',
        'contentSearchFilter',
        'contentSearchFilterText',
        'contentSearchFilterItems',
        'contentSearchColumn',
        'contentColumnsName',
        'isRowSelected'
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
    cellEditingStarted(event, edit) {
      this.gridEditing = true
      if (!edit) return

      // Store row node
      this.currentCellEditNode = this.gridApi.getSelectedNodes()[0]
    
      // Store row values
      if (Object.keys(this.currentCellEditValues).length == 0) {
        let node = this.gridApi.getSelectedNodes()[0].data
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
        this.gridApi.showLoadingOverlay()
        // Execute Query
        const payload = {
          server: this.serverSelected.id,
          database: this.database,
          queries: [query]
        }
        axios.post('/client/execute', payload)
          .then((response) => {
            this.gridApi.hideOverlay()
            let data = JSON.parse(response.data.data)
            // Build BottomBar
            this.parseContentBottomBar(data)
            // Check AUTO_INCREMENTs
            if (data[0].query.startsWith('INSERT')) node.setDataValue(this.contentPks[0], data[0].lastRowId)
          })
          .catch((error) => {
            this.gridApi.hideOverlay()
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
              this.showDialog(dialogOptions['mode'], dialogOptions['title'], dialogOptions['text'], dialogOptions['button1'], dialogOptions['button2'])
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
        let focused = this.gridApi.getFocusedCell()
        this.currentCellEditNode.setSelected(true)
        this.gridApi.setFocusedCell(focused.rowIndex, focused.column.colId)
        this.gridApi.startEditingCell({
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
      this.gridApi.showLoadingOverlay()
      // Build payload
      const payload = {
        server: this.serverSelected.id,
        database: this.database,
        table: this.treeviewSelected['name'],
        queries: ['SELECT * FROM ' + this.treeviewSelected['name'] + condition + ' LIMIT 1000;' ]
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          this.parseContentExecution(JSON.parse(response.data.data))
        })
        .catch((error) => {
          this.gridApi.hideOverlay()
          console.log(error)
          // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          // else this.notification(error.response.data.message, 'error')
        })
    },
    editDialogSubmit() {
      this.editDialog = false
      let nodes = this.gridApi.getSelectedNodes()
      for (let i = 0; i < nodes.length; ++i) nodes[i].setSelected(false)
      let focusedCell = this.gridApi.getFocusedCell()
      let currentNode = this.gridApi.getDisplayedRowAtIndex(focusedCell.rowIndex)
      currentNode.setSelected(true)
      currentNode.setDataValue(focusedCell.column.colId, this.editDialogEditor.getValue())
      setTimeout(() => {
        this.gridApi.startEditingCell({
          rowIndex: focusedCell.rowIndex,
          colKey: focusedCell.column.colId
        })
      }, 100)
    },
    editDialogCancel() {
      this.editDialog = false
      this.editDialogEditor.setValue('')
    },
  },
}
</script>