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
        <ag-grid-vue ref="agGridStructure" @grid-ready="onGridReady" @new-columns-loaded="onNewColumnsLoaded" @cell-key-down="onCellKeyDown" @row-double-clicked="onRowDoubleClicked" @row-drag-end="onRowDragEnd" style="width:100%; height:calc(100% - 48px);" class="ag-theme-alpine-dark" rowDragManaged="true" suppressMoveWhenRowDragging="true" rowHeight="35" headerHeight="35" rowSelection="single" rowDeselection="true" stopEditingWhenGridLosesFocus="true" :columnDefs="structureHeaders" :rowData="structureItems"></ag-grid-vue>      
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
    <!-------------------------------------->
    <!-- DIALOG: STRUCTURE ('new','edit') -->
    <!-------------------------------------->
    <v-dialog v-model="structureDialog" persistent max-width="60%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ structureDialogTitle }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="structureDialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form v-if="tabStructureSelected == 'columns'" ref="structureDialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <v-text-field v-model="structureDialogItem.name" :rules="[v => !!v || '']" label="Name" autofocus required style="padding-top:0px;"></v-text-field>
                  <v-autocomplete v-model="structureDialogItem.type" :items="server.columnTypes" :rules="[v => !!v || '']" label="Type" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                  <v-text-field v-model="structureDialogItem.length" label="Length" required style="padding-top:0px;"></v-text-field>
                  <v-autocomplete :disabled="!['CHAR','VARCHAR','TEXT','TINYTEXT','MEDIUMTEXT','LONGTEXT','SET','ENUM'].includes(structureDialogItem.type)" v-model="structureDialogItem.collation" :items="server.collations" label="Collation" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                  <v-text-field :disabled="structureDialogItem.auto_increment" v-model="structureDialogItem.default" label="Default" required style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="structureDialogItem.comment" label="Comment" required style="padding-top:0px;"></v-text-field>
                  <v-checkbox :disabled="!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT','DECIMAL','FLOAT','DOUBLE'].includes(structureDialogItem.type)" v-model="structureDialogItem.unsigned" label="Unsigned" color="info" style="margin-top:0px; padding-top:0px;" hide-details></v-checkbox>
                  <v-checkbox :disabled="!['DATETIME','TIMESTAMP'].includes(structureDialogItem.type)" v-model="structureDialogItem.current_timestamp" label="On Update Current Timestamp" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                  <v-checkbox :disabled="!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT'].includes(structureDialogItem.type)" v-model="structureDialogItem.auto_increment" label="Auto Increment" @change="structureDialogItem.auto_increment ? structureDialogItem.default = '' : ''" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                  <v-checkbox v-model="structureDialogItem.null" label="Allow Null" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                </v-form>
                <v-form v-else-if="tabStructureSelected == 'indexes'" ref="structureDialogForm" style="margin-top:10px; margin-bottom:5px;">
                  <v-text-field v-model="structureDialogItem.name" :rules="[v => !!v || '']" label="Name" autofocus required style="padding-top:0px;"></v-text-field>
                  <v-select v-model="structureDialogItem.type" :items="server.indexTypes" :rules="[v => !!v || '']" label="Type" auto-select-first required style="padding-top:0px;"></v-select>
                  <v-text-field v-model="structureDialogItem.fields" :rules="[v => !!v || '']" label="Fields" hint="Column names separated by comma. Example: col1, col2, col3" required style="padding-top:0px;"></v-text-field>
                </v-form>
                <v-form v-else-if="tabStructureSelected == 'fks'" ref="structureDialogForm" style="margin-bottom:15px;">
                  <v-card>
                    <v-toolbar flat dense height="42" color="#2e3131">
                      <div class="body-1">Table: {{ this.treeviewSelected['name'] }}</div>
                    </v-toolbar>
                    <v-card-text style="padding-bottom:0px;">
                      <v-text-field v-model="structureDialogItem.name" label="Name" autofocus required style="padding-top:0px;"></v-text-field>
                      <v-select v-model="structureDialogItem.column" :items="columnItems" :rules="[v => !!v || '']" label="Column" auto-select-first required style="padding-top:0px;"></v-select>
                    </v-card-text>
                  </v-card>
                  <v-card style="margin-top:10px;">
                    <v-toolbar flat dense height="42" color="#2e3131">
                      <div class="body-1">References</div>
                    </v-toolbar>
                    <v-card-text style="padding-bottom:0px;">
                      <v-select v-model="structureDialogItem.fk_table" :items="tableItems" :rules="[v => !!v || '']" label="Table" auto-select-first required style="padding-top:0px;"></v-select>
                      <v-text-field v-model="structureDialogItem.fk_column" label="Column" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                    </v-card-text>
                  </v-card>
                  <v-card style="margin-top:10px;">
                    <v-toolbar flat dense height="42" color="#2e3131">
                      <div class="body-1">Action</div>
                    </v-toolbar>
                    <v-card-text style="padding-bottom:0px;">
                      <v-select v-model="structureDialogItem.on_update" :items="server.fkRules" :rules="[v => !!v || '']" label="On update" auto-select-first required style="padding-top:0px;"></v-select>
                      <v-select v-model="structureDialogItem.on_delete" :items="server.fkRules" :rules="[v => !!v || '']" label="On delete" auto-select-first required style="padding-top:0px;"></v-select>
                    </v-card-text>
                  </v-card>
                </v-form>
                <v-form v-else-if="tabStructureSelected == 'triggers'" ref="structureDialogForm" style="margin-top:10px; margin-bottom:15px;">
                
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="structureDialogSubmit" color="primary">Save</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="structureDialogCancel" outlined color="#e74d3c">Cancel</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!------------------------------------>
    <!-- DIALOG: BASIC ('info','error') -->
    <!------------------------------------>
    <v-dialog v-model="dialog" persistent max-width="50%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">{{ dialogTitle }}</div>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:20px; margin-bottom:15px;">
                  <div v-if="dialogText.length > 0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogText }}</div>
                  <v-select v-if="dialogMode == 'export'" outlined v-model="dialogSelect" :items="['Meteor','JSON','CSV','SQL']" label="Format" hide-details></v-select>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col v-if="dialogSubmitText.length > 0" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="dialogSubmit" color="primary">{{ dialogSubmitText }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogCancelText.length > 0" style="margin-bottom:10px;">
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
      // Loading
      loading: false,
      // Dialog - Structure
      structureDialog: false,
      structureDialogMode: '',
      structureDialogItem: {},
      structureDialogTitle: '',
      // Indexes
      indexHeaders: [],
      indexItems: [],
      indexItem: [],
      indexMode: '',
      // Dialog - Basic
      dialog: false,
      dialogMode: '',
      dialogTitle: '',
      dialogText: '',
      dialogSelect: '',
      dialogSubmitText: '',
      dialogCancelText: '',
      // FK columns
      columnItems: [],
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
        'tabStructureSelected',
        'bottomBarStructure',
        'gridApi',
        'columnApi',
        'structureOrigin',
        'structureHeaders',
        'structureItems',
        'treeviewSelected',
        'server',
        'database',
        'tableItems',
    ], { path: 'client/connection' }),
  },
  mounted () {
    EventBus.$on('GET_STRUCTURE', this.getStructure);
  },
  watch: {
    structureDialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.structureDialogForm !== 'undefined') this.$refs.structureDialogForm.resetValidation()
        if (typeof this.$refs.structureDialogFormFocus !== 'undefined') this.$refs.structureDialogFormFocus.focus()
      })
    }
  },
  methods: {
   onGridReady(params) {
      this.gridApi.structure = params.api
      this.columnApi.structure = params.columnApi
      this.$refs['agGridStructure'].$el.addEventListener('click', this.onGridClick)
      this.gridApi.structure.showLoadingOverlay()
    },
    onNewColumnsLoaded() {
      if (this.gridApi.structure != null) this.resizeTable()
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
      if (this.tabStructureSelected == 'columns') this.editStructure(event.data)
    },
    onRowDragEnd(event) {
      if (event.overIndex - event.node.id == 0) return

      if (this.tabStructureSelected == 'columns') {
        this.structureDialogMode = 'drag'
        this.structureDialogSubmitColumns(event)
      }
    },
    addStructure() {
      var dialogOptions = {
        mode: 'new',
        title: this.tabStructureSelected == 'columns' ? 'New Column' : this.tabStructureSelected == 'indexes' ? 'New Index' : this.tabStructureSelected == 'fks' ? 'New Foreign Key' : 'New Trigger',
        item: {}
      }
      if (this.tabStructureSelected == 'columns') dialogOptions['item'] = { name: '', type: '', length: '', collation: '', default: '', comment: '', null: false, unsigned: false, current_timestamp: false, auto_increment: false }
      else if (this.tabStructureSelected == 'indexes') dialogOptions['item'] = { name: '', type: '', fields: '' }
      else if (this.tabStructureSelected == 'fks') dialogOptions['item'] = { name: '', column: '', fk_table: '', fk_column: '', on_update: '', on_delete: '' }
      this.showStructureDialog(dialogOptions)
    },
    removeStructure() {
      this.structureDialogMode = 'delete'
      let objectName = this.tabStructureSelected == 'columns' ? 'column' : this.tabStructureSelected == 'indexes' ? 'index' : this.tabStructureSelected == 'fks' ? 'foreign key' : 'trigger'
      var dialogOptions = {
        mode: 'delete',
        title: 'Delete ' + objectName + '?',
        text: "Are you sure you want to delete the " + objectName + " '" + this.gridApi.structure.getSelectedRows()[0].name + "' from this table? This action cannot be undone.",
        submit: 'Cancel',
        cancel: 'Delete'
      }
      this.showDialog(dialogOptions)
    },
    editStructure(data) {
      var dialogOptions = {
        mode: 'edit',
        title: this.tabStructureSelected == 'columns' ? 'Edit Column' : this.tabStructureSelected == 'indexes' ? 'Edit Index' : this.tabStructureSelected == 'fks' ? 'Edit Foreign Key' : 'Edit Trigger',
        item: {}
      }
      if (this.tabStructureSelected == 'columns') {
        dialogOptions['item'] = {
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
      }
      this.showStructureDialog(dialogOptions)
    },
    structureDialogSubmit() {
      if (this.tabStructureSelected == 'columns') this.structureDialogSubmitColumns()
      else if (this.tabStructureSelected == 'indexes') this.structureDialogSubmitIndexes()
      else if (this.tabStructureSelected == 'fks') this.structureDialogSubmitFks()
      else if (this.tabStructureSelected == 'triggers') this.structureDialogSubmitTriggers()
    },
    structureDialogCancel() {
      this.structureDialog = false
    },
    structureDialogSubmitColumns(event) {
      // Check if all fields are filled
      if (!this.$refs.structureDialogForm.validate()) {
        EventBus.$emit('NOTIFICATION', 'Please make sure all required fields are filled out correctly', 'error')
        return
      }
      this.loading = true
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
          this.loading = false
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

      // Execute queries
      this.execute([query])
    },
    structureDialogSubmitIndexes() {
      // Check if all fields are filled
      if (!this.$refs.structureDialogForm.validate()) {
        EventBus.$emit('NOTIFICATION', 'Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Build query
      this.loading = true
      var query = []
      if (this.structureDialogMode == 'new') {
        query.push("ALTER TABLE " + this.treeviewSelected['name'] + " ADD " + this.structureDialogItem.type + ' ' + this.structureDialogItem.name + "(" + this.structureDialogItem.fields + ");")
      }
      else if (this.structureDialogMode == 'delete') {
        let row = this.gridApi.structure.getSelectedRows()[0]
        query.push("ALTER TABLE " + this.treeviewSelected['name'] + " DROP INDEX " + row.name + ';')
      }
      // Execute query
      this.execute(query)
    },
    structureDialogSubmitFks() {
      // Check if all fields are filled
      if (!this.$refs.structureDialogForm.validate()) {
        EventBus.$emit('NOTIFICATION', 'Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Build query
      let query = []
      if (this.structureDialogMode == 'new') {
        let constraintName = (this.structureDialogItem.name.length > 0) ? 'CONSTRAINT ' + this.structureDialogItem.name : ''
        query.push("ALTER TABLE " + this.treeviewSelected['name'] + " ADD " + constraintName + " FOREIGN KEY(" + this.structureDialogItem.column + ") REFERENCES " + this.structureDialogItem.fk_table + "(" + this.structureDialogItem.fk_column + ");")
      }
      else if (this.structureDialogMode == 'delete') {
        let row = this.gridApi.structure.getSelectedRows()[0]
        console.log(row)
        return
        // query.push("ALTER TABLE " + this.treeviewSelected['name'] + " DROP FOREIGN KEY " +  + ";")
      }
      // Execute query
      this.execute(query)
    },
    structureDialogSubmitTriggers() {

    },
    getStructure() {
      this.gridApi.structure.showLoadingOverlay()
      this.bottomBarStructure = { status: '', text: '', info: '' }
      // Retrieve Tables
      axios.get('/client/structure', { params: { server: this.server.id, database: this.database, table: this.treeviewSelected['name'] } })
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
          this.loading = false
        })
    },
    parseStructure(data) {
      // Parse Columns
      var columns_items = JSON.parse(data.columns)
      var columns_headers = []
      var column_names = []
      if (columns_items.length > 0) {
        var columns_keys = Object.keys(columns_items[0])
        for (let i = 0; i < columns_keys.length; ++i) {
          let field = columns_keys[i].trim()
          columns_headers.push({ headerName: columns_keys[i], colId: field, field: field, sortable: false, filter: false, resizable: true, editable: false })
        }
        for (let i = 0; i < columns_items.length; ++i) {
          column_names.push(columns_items[i]['name'])
        }
      }
      columns_headers[0]['rowDrag'] = true
      this.structureOrigin['columns'] = { headers: columns_headers, items: columns_items }
      this.columnItems = column_names

      // show 'no rows' overlay
      // this.gridApi.structure.showNoRowsOverlay()

      // Parse Indexes
      var indexes_items = JSON.parse(data.indexes)
      var indexes_headers = []
      if (indexes_items.length > 0) {
        var indexes_keys = Object.keys(indexes_items[0])
        for (let i = 0; i < indexes_keys.length; ++i) {
          let field = indexes_keys[i].trim()
          indexes_headers.push({ headerName: indexes_keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: false })
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
          fks_headers.push({ headerName: fks_keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: false })
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
          triggers_headers.push({ headerName: triggers_keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: false })
        }
      }
      this.structureOrigin['triggers'] = { headers: triggers_headers, items: triggers_items } 

      // Show Data
      if (this.tabStructureSelected == 'columns') this.tabStructureColumns()
      else if (this.tabStructureSelected == 'indexes') this.tabStructureIndexes()
      else if (this.tabStructureSelected == 'fks') this.tabStructureFK()
      else if (this.tabStructureSelected == 'triggers') this.tabStructureTriggers()
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
      this.gridApi.structure.setColumnDefs(this.structureHeaders)
    },
    tabStructureIndexes() {
      this.tabStructureSelected = 'indexes'
      this.structureHeaders = this.structureOrigin['indexes']['headers'].slice(0)
      this.structureItems = this.structureOrigin['indexes']['items'].slice(0)
      this.gridApi.structure.setColumnDefs(this.structureHeaders)
    },
    tabStructureFK() {
      this.tabStructureSelected = 'fks'
      this.structureHeaders = this.structureOrigin['fks']['headers'].slice(0)
      this.structureItems = this.structureOrigin['fks']['items'].slice(0)
      this.gridApi.structure.setColumnDefs(this.structureHeaders)
    },
    tabStructureTriggers() {
      this.tabStructureSelected = 'triggers'
      this.structureHeaders = this.structureOrigin['triggers']['headers'].slice(0)
      this.structureItems = this.structureOrigin['triggers']['items'].slice(0)
      this.gridApi.structure.setColumnDefs(this.structureHeaders)
    },
    showDialog(options) {
      this.dialogMode = options.mode
      this.dialogTitle = options.title
      this.dialogText = options.text
      this.dialogSubmitText = options.submit
      this.dialogCancelText = options.cancel
      this.dialog = true
    },
    dialogSubmit() {
      this.dialog = false
    },
    dialogCancel() {
      if (this.dialogMode == 'delete') {
        if (this.tabStructureSelected == 'columns') this.structureDialogSubmitColumns()
        else if (this.tabStructureSelected == 'indexes') this.structureDialogSubmitIndexes()
        else if (this.tabStructureSelected == 'fks') this.structureDialogSubmitFks()
        else if (this.tabStructureSelected == 'triggers') this.structureDialogSubmitTriggers()
      }
    },
    showStructureDialog(options) {
      this.structureDialogMode = options.mode
      this.structureDialogTitle = options.title
      this.structureDialogItem = options.item
      this.structureDialog = true
    },
    execute(queries) {
      // Show Loading Overlay
      this.gridApi.structure.showLoadingOverlay()

      // Execute Query
      const payload = {
        server: this.server.id,
        database: this.database,
        queries: queries
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          // Hide Dialogs
          this.dialog = false
          this.structureDialog = false
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
            // Show last error
            let data = JSON.parse(error.response.data.data)
            let error = ''
            for (let i = data.length - 1; i >=0 ; i--) {
              if (data[i]['error'] !== undefined) { 
                error = data[i]['error']
                break
              }
            }
            let dialogOptions = {
              mode: 'info',
              title: 'Unable to apply changes',
              text: error,
              submit: 'Close',
              cancel: ''
            }
            this.showDialog(dialogOptions)
            // Build BottomBar
            this.parseStructureBottomBar(data)
            this.loading = false
          }
        })
    }
  },
}
</script>