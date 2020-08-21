<template>
  <div style="height:100%">
    <!--------------->
    <!-- STRUCTURE -->
    <!--------------->
    <div style="height:calc(100% - 36px)">
      <div style="width:100%; height:100%;">
        <v-tabs show-arrows dense background-color="#303030" color="white" slider-color="white" slider-size="1" slot="extension" class="elevation-2">
        <v-tabs-slider></v-tabs-slider>
        <v-tab @click="tabStructureColumns()"><span class="pl-2 pr-2">Columns</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab @click="tabStructureIndexes()"><span class="pl-2 pr-2">Indexes</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab @click="tabStructureFK()"><span class="pl-2 pr-2">Foreign Keys</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab @click="tabStructureTriggers()"><span class="pl-2 pr-2">Triggers</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        </v-tabs>
        <ag-grid-vue ref="agGridStructure" @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" @row-double-clicked="onRowDoubleClicked" @row-drag-end="onRowDragEnd" style="width:100%; height:calc(100% - 48px);" class="ag-theme-alpine-dark" suppressNoRowsOverlay="true" rowDragManaged="true" suppressMoveWhenRowDragging="true" rowHeight="35" headerHeight="35" rowSelection="simple" :stopEditingWhenGridLosesFocus="true" :columnDefs="structureHeaders" :rowData="structureItems"></ag-grid-vue>
      </div>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn @click="addStructure" text small :title="tabStructureSelected == 'columns' ? 'New Column' : tabStructureSelected == 'indexes' ? 'New Index' : tabStructureSelected == 'fks' ? 'New Foreign Key' : 'New Trigger'" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="removeStructure" text small :title="tabStructureSelected == 'columns' ? 'Remove Column' : tabStructureSelected == 'indexes' ? 'Remove Index' : tabStructureSelected == 'fks' ? 'Remove Foreign Key' : 'Remove Trigger'" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="getStructure" text small :title="tabStructureSelected == 'columns' ? 'Refresh Columns' : tabStructureSelected == 'indexes' ? 'Refresh Indexes' : tabStructureSelected == 'fks' ? 'Refresh Foreign Keys' : 'Refresh Triggers'" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            <v-icon v-if="bottomBarStructure['status']=='success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:5px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBarStructure['status']=='failure'" title="Failed" small style="color:rgb(231, 76, 60); padding-bottom:1px; padding-right:5px;">fas fa-times-circle</v-icon>
            <span :title="bottomBarStructure['text']">{{ bottomBarStructure['text'] }}</span>
          </div>
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBarStructure['info'] }}</div>
        </v-col>
      </v-row>
    </div>
    <!------------->
    <!-- DIALOGS -->
    <!------------->
    <v-dialog v-model="structureDialog" persistent max-width="60%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ structureDialogTitle }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loadingDialog" @click="structureDialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form v-if="tabStructureSelected == 'columns'" ref="structureDialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <v-text-field ref="structureDialogFormFocus" v-model="structureDialogItem.name" :rules="[v => !!v || '']" label="Name" required style="padding-top:0px;"></v-text-field>
                  <v-autocomplete v-model="structureDialogItem.type" :items="structureDialogColumnTypes" :rules="[v => !!v || '']" label="Type" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                  <v-text-field v-model="structureDialogItem.length" label="Length" required style="padding-top:0px;"></v-text-field>
                  <v-autocomplete :disabled="!['CHAR','VARCHAR','TEXT','TINYTEXT','MEDIUMTEXT','LONGTEXT','SET','ENUM'].includes(structureDialogItem.type)" v-model="structureDialogItem.collation" :items="structureDialogCollations" label="Collation" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                  <v-text-field :disabled="structureDialogItem.auto_increment" v-model="structureDialogItem.default" label="Default" required style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="structureDialogItem.comment" label="Comment" required style="padding-top:0px;"></v-text-field>
                  <v-checkbox :disabled="!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT','DECIMAL','FLOAT','DOUBLE'].includes(structureDialogItem.type)" v-model="structureDialogItem.unsigned" label="Unsigned" color="info" style="margin-top:0px; padding-top:0px;" hide-details></v-checkbox>
                  <v-checkbox :disabled="!['DATETIME','TIMESTAMP'].includes(structureDialogItem.type)" v-model="structureDialogItem.current_timestamp" label="On Update Current Timestamp" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                  <v-checkbox :disabled="!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT'].includes(structureDialogItem.type)" v-model="structureDialogItem.auto_increment" label="Auto Increment" @change="structureDialogItem.auto_increment ? structureDialogItem.default = '' : ''" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                  <v-checkbox v-model="structureDialogItem.null" label="Allow Null" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loadingDialog" @click="structureDialogSubmit" color="primary">Save</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loadingDialog" @click="structureDialogCancel" outlined color="#e74d3c">Cancel</v-btn>
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
        'tabStructureSelected',
        'loadingDialog',
        'structureDialog',
        'structureDialogTitle',
        'structureDialogItem',
        'structureDialogColumnTypes',
        'structureDialogCollations',
        'bottomBarStructure',
        'gridApi',
        'columnApi',
        'structureOrigin',
        'structureHeaders',
        'structureItems',
        'treeviewSelected',
        'server',
        'database',
    ], { path: 'client/connection' }),
  },
  mounted () {
    EventBus.$on('GET_STRUCTURE', this.getStructure);
  },
  methods: {
   onGridReady(params) {
      this.gridApi.structure = params.api
      this.columnApi.structure = params.columnApi
      this.$refs['agGridStructure'].$el.addEventListener('click', this.onGridClick)
      this.gridApi.structure.showLoadingOverlay()
    },
    onGridClick(event) {
      if (event.target.className == 'ag-center-cols-viewport') {
        this.gridApi.structure.deselectAll()
      }
    },
    resizeTable() {
      var allColumnIds = [];
      this.columnApi.structure.getAllColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi.structure.autoSizeColumns(allColumnIds);
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

      if (this.tabStructureSelected == 'columns') {
        this.structureDialogMode = 'drag'
        this.structureDialogSubmitColumns(event)
      }
    },
    addStructure() {
      this.structureDialogMode = 'new'
      this.structureDialogTitle = this.tabStructureSelected == 'columns' ? 'New Column' : this.tabStructureSelected == 'indexes' ? 'New Index' : this.tabStructureSelected == 'fks' ? 'New Foreign Key' : 'New Trigger'
      this.structureDialogItem = { name: '', type: '', length: '', collation: '', default: '', comment: '', null: false, unsigned: false, current_timestamp: false, auto_increment: false }
      this.structureDialog = true
    },
    removeStructure() {
      this.structureDialogMode = 'delete'
      // Show confirmation dialog
      var dialogOptions = {
        'mode': 'removeColumnsConfirm',
        'title': 'Delete columns?',
        'text': "Are you sure you want to delete the column '" + this.gridApi.structure.getSelectedRows()[0].name + "' from this table? This action cannot be undone.",
        'button1': 'Cancel',
        'button2': 'Delete'
      }
      this.showDialog(dialogOptions['mode'], dialogOptions['title'], dialogOptions['text'], dialogOptions['button1'], dialogOptions['button2'])
    },
    editStructure(data) {
      this.structureDialogMode = 'edit'
      this.structureDialogTitle = this.tabStructureSelected == 'columns' ? 'Edit Column' : this.tabStructureSelected == 'indexes' ? 'Edit Index' : this.tabStructureSelected == 'fks' ? 'Edit Foreign Key' : 'Edit Trigger'
      this.structureDialogItem = { 
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
      }
      this.structureDialog = true
    },
    structureDialogSubmit() {
      if (this.tabStructureSelected == 'columns') this.structureDialogSubmitColumns()
    },
    structureDialogSubmitColumns(event) {
      this.loadingDialog = true
      let query = 'ALTER TABLE ' + this.treeviewSelected['name']

      if (['new','edit'].includes(this.structureDialogMode)) {
        // Parse Form Fields
        if (!['CHAR','VARCHAR','TEXT','TINYTEXT','MEDIUMTEXT','LONGTEXT','ENUM','SET'].includes(this.structureDialogItem.type)) this.structureDialogItem.collation = ''
        if (!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT','DECIMAL','FLOAT','DOUBLE'].includes(this.structureDialogItem.type)) this.structureDialogItem.unsigned = false
        if (!['DATETIME','TIMESTAMP'].includes(this.structureDialogItem.type)) this.structureDialogItem.current_timestamp = false
        if (!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT'].includes(this.structureDialogItem.type)) this.structureDialogItem.auto_increment = false

        // Check if all fields are filled
        if (!this.$refs.structureDialogForm.validate()) {
          this.notification('Please make sure all required fields are filled out correctly', 'error')
          this.loadingDialog = false
          return
        }

        // Build Query
        if (this.structureDialogMode == 'new') query += ' ADD ' + this.structureDialogItem.name
        else if (this.structureDialogMode == 'edit') query += ' CHANGE ' + this.gridApi.structure.getSelectedRows()[0].name  + ' ' + this.structureDialogItem.name
        query += ' ' + this.structureDialogItem.type 
          + (this.structureDialogItem.length.length > 0 ? (this.structureDialogItem.length.indexOf(',') == -1) ? '(' + this.structureDialogItem.length + ')' : '(' + this.structureDialogItem.length.split(",").map(item => "'" + item.trim() + "'") + ')' : '')
          + (this.structureDialogItem.unsigned ? ' UNSIGNED' : '')
          + (this.structureDialogItem.collation.length > 0 ? ' CHARACTER SET ' + this.structureDialogItem.collation.split('_')[0] + ' COLLATE ' + this.structureDialogItem.collation : '')
          + (this.structureDialogItem.null ? ' NULL' : ' NOT NULL')
          + (this.structureDialogItem.default.length > 0 ? " DEFAULT" + (this.structureDialogItem.default == 'CURRENT_TIMESTAMP' ? ' CURRENT_TIMESTAMP' : " '" + this.structureDialogItem.default + "'") : '')
          + (this.structureDialogItem.current_timestamp ? ' ON UPDATE CURRENT_TIMESTAMP' : '')
          + (this.structureDialogItem.auto_increment ? ' AUTO_INCREMENT' : '')
          + (this.structureDialogItem.comment ? " COMMENT '" + this.structureDialogItem.comment + "'" : '')
      }
      else if (this.structureDialogMode == 'delete') query += ' DROP COLUMN ' + this.gridApi.structure.getSelectedRows()[0].name
      else if (this.structureDialogMode == 'drag') {
        query += ' MODIFY ' + this.gridApi.structure.getDisplayedRowAtIndex(event.node.rowIndex).data.name
          + ' ' + event.node.data.type 
          + (event.node.data.length !== null ? '(' + event.node.data.length + ')' : '')
          + (event.node.data.unsigned ? ' UNSIGNED' : '')
          + (event.node.data.collation !== null ? ' CHARACTER SET ' + event.node.data.collation.split('_')[0] + ' COLLATE ' + event.node.data.collation : '')
          + (event.node.data.allow_null ? ' NULL' : ' NOT NULL')
          + (event.node.data.default !== null ? " DEFAULT" + (event.node.data.default == 'CURRENT_TIMESTAMP' ? ' CURRENT_TIMESTAMP' : " '" + event.node.data.default + "'") : '')
          + (event.node.data.extra.toLowerCase() == 'on update current_timestamp' ? ' ON UPDATE CURRENT_TIMESTAMP' : '')
          + (event.node.data.extra.toLowerCase() ==  'auto_increment' ? ' AUTO_INCREMENT' : '')
          + (event.node.data.comment ? " COMMENT '" + event.node.data.comment + "'" : '')
          + (event.node.rowIndex == 0 ? ' FIRST' : ' AFTER ' + this.gridApi.structure.getDisplayedRowAtIndex(event.node.rowIndex - 1).data.name)
      }
      query += ';'

      // Show Loading Overlay
      this.gridApi.structure.showLoadingOverlay()

      // Execute Query
      const payload = {
        server: this.server.id,
        database: this.database,
        queries: [query]
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          // Get Response Data
          let data = JSON.parse(response.data.data)
          // Get Structure
          this.getStructure()
          // Build BottomBar
          this.parseStructureBottomBar(data)
        })
        .catch((error) => {
          this.gridApi.structure.hideOverlay()
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else {
            // Show error
            let data = JSON.parse(error.response.data.data)
            let dialogOptions = {
              'mode': 'info',
              'title': 'Unable to apply changes',
              'text': data[0]['error'],
              'button1': 'Close',
              'button2': ''
            }
            this.showDialog(dialogOptions['mode'], dialogOptions['title'], dialogOptions['text'], dialogOptions['button1'], dialogOptions['button2'])
            // Build BottomBar
            this.parseStructureBottomBar(data)
            this.loadingDialog = false
          }
        })
    },
    structureDialogCancel() {
      this.structureDialog = false
    },
    getStructure() {
      this.gridApi.structure.showLoadingOverlay()
      this.bottomBarStructure = { status: '', text: '', info: '' }
      // Retrieve Tables
      const table = this.treeviewSelected['name']
      axios.get('/client/structure', { params: { server: this.server.id, database: this.database, table: table } })
        .then((response) => {
          this.parseStructure(response.data)
        })
        .catch((error) => {
          console.log(error)
          // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          // else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.gridApi.structure.hideOverlay()
          this.loadingDialog = false
          this.dialog = false
          this.structureDialog = false
        })
    },
    parseStructure(data) {
      // Parse Columns
      var columns_items = JSON.parse(data.columns)
      var columns_headers = []
      if (columns_items.length > 0) {
        var columns_keys = Object.keys(columns_items[0])
        for (let i = 0; i < columns_keys.length; ++i) {
          let field = columns_keys[i].trim()
          columns_headers.push({ headerName: columns_keys[i], colId: field, field: field, sortable: false, filter: false, resizable: true, editable: false })
        }
      }
      columns_headers[0]['rowDrag'] = true
      this.structureOrigin['columns'] = { headers: columns_headers, items: columns_items }

      // show 'no rows' overlay
      // this.gridApi.structure.showNoRowsOverlay()

      // Parse Indexes
      var indexes_items = JSON.parse(data.indexes)
      var indexes_headers = []
      if (indexes_items.length > 0) {
        var indexes_keys = Object.keys(indexes_items[0])
        for (let i = 0; i < indexes_keys.length; ++i) {
          let field = indexes_keys[i].trim()
          indexes_headers.push({ headerName: indexes_keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: true })
        }
      }
      this.structureOrigin['indexes'] = { headers: indexes_headers, items: indexes_items }

      // Parse Foreign Keys
      var fks_items = JSON.parse(data.fks)
      var fks_headers = []
      if (fks_items.length > 0) {
        var fks_keys = Object.keys(fks_items[0])
        for (let i = 0; i < fks_keys.length; ++i) {
          let field = fks_keys[i].trim()
          fks_headers.push({ headerName: fks_keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: true })
        }
      }
      this.structureOrigin['fks'] = { headers: fks_headers, items: fks_items } 

      // Parse Triggers
      var triggers_items = JSON.parse(data.triggers)
      var triggers_headers = []
      if (triggers_items.length > 0) {
        var triggers_keys = Object.keys(triggers_items[0])
        for (let i = 0; i < triggers_keys.length; ++i) {
          let field = triggers_keys[i].trim()
          triggers_headers.push({ headerName: triggers_keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: true })
        }
      }
      this.structureOrigin['triggers'] = { headers: triggers_headers, items: triggers_items } 

      // Show Data
      if (this.tabStructureSelected == 'columns') this.tabStructureColumns()
      else if (this.tabStructureSelected == 'indexes') this.tabStructureIndexes()
      else if (this.tabStructureSelected == 'fks') this.tabStructureFK()
      else if (this.tabStructureSelected == 'triggers') this.tabStructureTriggers()

      // Resize Table
      // this.gridApi.structure.setColumnDefs(headers)
      this.resizeTable()
    },
    parseStructureBottomBar(data) {
      var elapsed = null
      if (data[data.length-1]['time'] !== undefined) {
        elapsed = 0
        for (let i = 0; i < data.length; ++i) {
          elapsed += parseFloat(data[i]['time'])
        }
        elapsed /= data.length
      }
      this.bottomBarStructure['status'] = data[0]['error'] === undefined ? 'success' : 'failure'
      this.bottomBarStructure['text'] = data[0]['query']
      if (elapsed != null) this.bottomBarStructure['info'] = elapsed.toString() + 's elapsed'
    },
    tabStructureColumns() {
      this.tabStructureSelected = 'columns'
      this.structureHeaders = this.structureOrigin['columns']['headers'].slice(0)
      this.structureItems = this.structureOrigin['columns']['items'].slice(0)
    },
    tabStructureIndexes() {
      this.tabStructureSelected = 'indexes'
      this.structureHeaders = this.structureOrigin['indexes']['headers'].slice(0)
      this.structureItems = this.structureOrigin['indexes']['items'].slice(0)
    },
    tabStructureFK() {
      this.tabStructureSelected = 'fks'
      this.structureHeaders = this.structureOrigin['fks']['headers'].slice(0)
      this.structureItems = this.structureOrigin['fks']['items'].slice(0)
    },
    tabStructureTriggers() {
      this.tabStructureSelected = 'triggers'
      this.structureHeaders = this.structureOrigin['triggers']['headers'].slice(0)
      this.structureItems = this.structureOrigin['triggers']['items'].slice(0)
    },
  },
}
</script>