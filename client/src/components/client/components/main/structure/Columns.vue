<template>
  <div style="height:100%">
    <!------------->
    <!-- COLUMNS -->
    <!------------->
    <div style="height:calc(100% - 84px)">
      <ag-grid-vue ref="agGridStructureColumns" suppressDragLeaveHidesColumns suppressFieldDotNotation suppressContextMenu preventDefaultOnContextMenu oncontextmenu="return false" @grid-ready="onGridReady" @new-columns-loaded="onNewColumnsLoaded" @cell-key-down="onCellKeyDown" @cell-clicked="onCellClicked" @row-double-clicked="onRowDoubleClicked" @row-drag-end="onRowDragEnd" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowDragManaged="true" suppressMoveWhenRowDragging="true" rowHeight="35" headerHeight="35" rowSelection="single" rowDeselection="true" stopEditingWhenCellsLoseFocus="true" :columnDefs="structureHeaders.columns" :rowData="structureItems.columns"></ag-grid-vue>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn @click="refreshColumns" text small title="Refresh Columns" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="addColumn" text small title="New Column" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn :disabled="!selectedRows" @click="removeColumn" text small title="Remove Column" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            <v-icon v-if="bottomBar.structure.columns['status'] == 'success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:7px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBar.structure.columns['status'] == 'failure'" title="Failed" small style="color:#EF5354; padding-bottom:1px; padding-right:7px;">fas fa-times-circle</v-icon>
            <span :title="bottomBar.structure.columns['text']">{{ bottomBar.structure.columns['text'] }}</span>
          </div>
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBar.structure.columns['info'] }}</div>
        </v-col>
      </v-row>
    </div>
    <!------------------------------->
    <!-- DIALOG: new, edit, delete -->
    <!------------------------------->
    <v-dialog v-model="dialog" max-width="60%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; padding-bottom:3px">{{ dialogOptions.icon }}</v-icon>{{ dialogOptions.title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <div v-if="dialogOptions.text.length > 0" class="body-1">{{ dialogOptions.text }}</div>
                <v-form ref="dialogForm" style="margin-top:15px; margin-bottom:15px;">
                  <div v-if="Object.keys(dialogOptions.item).length > 0">
                    <v-text-field v-model="dialogOptions.item.name" :rules="[v => !!v || '']" label="Name" autofocus required style="padding-top:0px;"></v-text-field>
                    <v-autocomplete v-model="dialogOptions.item.type" :items="server.columnTypes" :rules="[v => !!v || '']" label="Type" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                    <v-text-field v-model="dialogOptions.item.length" label="Length" required style="padding-top:0px;"></v-text-field>
                    <v-text-field :disabled="dialogOptions.item.auto_increment" v-model="dialogOptions.item.default" label="Default" required style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="dialogOptions.item.comment" label="Comment" required style="padding-top:0px;"></v-text-field>
                    <v-autocomplete :disabled="!['CHAR','VARCHAR','TEXT','TINYTEXT','MEDIUMTEXT','LONGTEXT','SET','ENUM'].includes(dialogOptions.item.type)" @change="getCollations" v-model="dialogOptions.item.encoding" :items="encodings" label="Encoding" auto-select-first required style="padding-top:5px;"></v-autocomplete>
                    <v-autocomplete :disabled="!['CHAR','VARCHAR','TEXT','TINYTEXT','MEDIUMTEXT','LONGTEXT','SET','ENUM'].includes(dialogOptions.item.type) || loading" :loading="loading" v-model="dialogOptions.item.collation" :items="collations" :rules="[v => !!v || '']" label="Collation" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                    <v-checkbox :disabled="!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT','DECIMAL','FLOAT','DOUBLE'].includes(dialogOptions.item.type)" v-model="dialogOptions.item.unsigned" label="Unsigned" color="info" style="margin-top:0px; padding-top:0px;" hide-details></v-checkbox>
                    <v-checkbox :disabled="!['DATETIME','TIMESTAMP'].includes(dialogOptions.item.type)" v-model="dialogOptions.item.current_timestamp" label="On Update Current Timestamp" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                    <v-checkbox :disabled="!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT'].includes(dialogOptions.item.type)" v-model="dialogOptions.item.auto_increment" label="Auto Increment" @change="dialogOptions.item.auto_increment ? dialogOptions.item.default = '' : ''" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                    <v-checkbox v-model="dialogOptions.item.null" label="Allow Null" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px">
                  <v-row no-gutters>
                    <v-col v-if="dialogOptions.submit.length > 0" cols="auto" style="margin-right:5px;">
                      <v-btn :loading="loading" @click="dialogSubmit" color="#00b16a">{{ dialogOptions.submit }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogOptions.cancel.length > 0">
                      <v-btn :loading="loading2" @click="dialogCancel" color="#EF5354">{{ dialogOptions.cancel }}</v-btn>
                    </v-col>
                    <v-col v-if="loading" cols="auto" class="flex-grow-0 flex-shrink-0">
                      <v-progress-circular indeterminate color="white" size="15" width="1.5" style="height:100%"></v-progress-circular>
                    </v-col>
                    <v-col v-if="loading" cols="auto" class="flex-grow-0 flex-shrink-0" style="padding-left:10px">
                      <div class="body-2" style="height:100%; display:flex; align-items:center">{{ loadingText }}</div>
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
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      // Loading
      loading: false,
      loading2: false,
      loadingText: 'Applying changes...',
      // Dialog
      dialog: false,
      dialogOptions: { mode: '', title: '', text: '', item: {}, submit: '', cancel: '' },
      encodings: [],
      collations: [],
      // AG Grid
      selectedRows: false,
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'structureHeaders',
      'structureItems',
      'sidebarSelected',
      'server',
      'bottomBar',
      'headerTabSelected',
      'tabStructureSelected',
    ], { path: 'client/connection' }),
    ...mapFields([
      'gridApi',
      'columnApi',
    ], { path: 'client/components' }),
  },
  watch: {
    dialog (val) {
      this.dialogOpened = val
      if (!val) return
      this.buildSelectors()
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
    },
    headerTabSelected(val) {
      if (val == 'structure') {
        this.$nextTick(() => {
          if (this.gridApi.structure.columns != null) this.resizeTable()
        })
      }
    },
    tabStructureSelected(val) {
      if (val == 'columns') {
        this.$nextTick(() => { this.resizeTable() })
      }
    },
    "structureItems.columns" () {
      this.selectedRows = false
    },
  },
  methods: {
    buildSelectors() {
      // Build Encodings
      this.encodings = [{ text: 'Default (' + this.server.defaults.encoding + ')', value: this.server.defaults.encoding }]
      this.encodings.push({ divider: true })
      this.encodings.push(...this.server.encodings.reduce((acc, val) => { 
        acc.push({ text: val.description + ' (' + val.encoding + ')', value: val.encoding })
        return acc
      }, []))
      if (this.dialogOptions.item.encoding.length == 0) this.dialogOptions.item.encoding = this.encodings[0].value

      // Build Collations
      let item = (this.dialogOptions.item.encoding.length != 0) ? this.dialogOptions.item.encoding : this.server.defaults.encoding
      this.getCollations(item)
    },
    getCollations(encoding) {
      // Retrieve Databases
      this.loading = true
      const payload = {
        connection: this.id + '-shared',
        server: this.server.id, 
        encoding: encoding
      }
      axios.get('/client/collations', { params: payload })
        .then((response) => {
          this.parseCollations(encoding, response.data.collations)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message, '#EF5354')
        })
        .finally(() => {
          this.loading = false
        })
    },
    parseCollations(encoding, data) {
      let def = this.server.encodings.filter(obj => { return obj.encoding == encoding })[0]
      this.collations = [{ text: 'Default (' + def.collation + ')', value: def.collation }, { divider: true }, ...JSON.parse(data)]
      if (this.dialogOptions.item.collation.length == 0) this.dialogOptions.item.collation = this.collations[0].value
    },
    onGridReady(params) {
      this.gridApi.structure.columns = params.api
      this.columnApi.structure.columns = params.columnApi
      this.$refs['agGridStructureColumns'].$el.addEventListener('click', this.onGridClick)
    },
    onNewColumnsLoaded() {
      if (this.gridApi.structure.columns != null) this.resizeTable()
    },
    onGridClick(event) {
      if (event.target.className == 'ag-center-cols-viewport') {
        this.gridApi.structure.columns.deselectAll()
        this.selectedRows = false
      }
    },
    resizeTable() {
      var allColumnIds = [];
      this.columnApi.structure.columns.getColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi.structure.columns.autoSizeColumns(allColumnIds);
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        let selectedRows = this.gridApi.structure.columns.getSelectedRows()
        if (selectedRows.length > 1) {
          // Copy values
          let header = Object.keys(selectedRows[0])
          let value = selectedRows.map(row => header.map(fieldName => row[fieldName] == null ? 'NULL' : row[fieldName]).join('\t')).join('\n')
          navigator.clipboard.writeText(value)
          // Apply effect
          // this.gridApi.structure.columns.flashCells({
          //   rowNodes: this.gridApi.structure.columns.getSelectedNodes(),
          //   flashDelay: 200,
          //   fadeDelay: 200,
          // })
        }
        else {
          // Copy value
          navigator.clipboard.writeText(e.value)
          // Apply effect
          this.gridApi.structure.columns.flashCells({
            rowNodes: this.gridApi.structure.columns.getSelectedNodes(),
            columns: [this.gridApi.structure.columns.getFocusedCell().column.colId],
            flashDelay: 200,
            fadeDelay: 200,
          })
        }
      }
      else if (e.event.key == "Enter") this.editColumn(e.data)
      else if (['ArrowUp','ArrowDown'].includes(e.event.key)) {
        let cell = this.gridApi.structure.columns.getFocusedCell()
        let row = this.gridApi.structure.columns.getDisplayedRowAtIndex(cell.rowIndex)
        let node = this.gridApi.structure.columns.getRowNode(row.id)
        this.gridApi.structure.columns.deselectAll()
        node.setSelected(true)
      }
    },
    onCellClicked() {
      this.selectedRows = this.gridApi.structure.columns.getSelectedRows().length != 0
    },
    onRowDoubleClicked(event) {
      this.editColumn(event.data)
    },
    onRowDragEnd(event) {
      if (event.overIndex - event.node.id == 0) return
      this.dialogOptions.mode = 'drag'
      this.dialogSubmit(event)
    },
    addColumn() {
      this.dialogOptions = {
        mode: 'new',
        icon: 'fas fa-plus',
        title: 'NEW COLUMN',
        text: '',
        item: { name: '', type: '', length: '', default: '', comment: '', encoding: '', collation: '', null: false, unsigned: false, current_timestamp: false, auto_increment: false },
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialog = true
    },
    editColumn(data) {
      this.dialogOptions = {
        mode: 'edit',
        icon: 'fas fa-feather-alt',
        title: 'EDIT COLUMN',
        text: '',
        item: {
          name: data['Name'], 
          type: data['Type'], 
          length: (data['Length'] == null) ? '' : ['ENUM','SET'].includes(data['Type']) ? data['Length'].replaceAll("'",'') : data['Length'], 
          encoding: (data['Encoding'] == null) ? '' : data['Encoding'],
          collation: (data['Collation'] == null) ? '' : data['Collation'], 
          default: (data['Default'] == null) ? '' : data['Default'], 
          comment: (data['Comment'] == null) ? '' : data['Comment'], 
          null: data['Allow NULL'], 
          unsigned: data['Unsigned'], 
          current_timestamp: data['Extra'].toLowerCase() == 'on update current_timestamp', 
          auto_increment: data['Extra'].toLowerCase() == 'auto_increment'
        },
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialog = true
    },
    removeColumn() {
      this.dialogOptions = {
        mode: 'delete',
        icon: 'fas fa-minus',
        title: 'DELETE COLUMN',
        text: "Are you sure you want to delete the column '" + this.gridApi.structure.columns.getSelectedRows()[0].Name + "' from this table? This action cannot be undone.",
        item: {},
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialog = true
    },
    refreshColumns() {
      EventBus.$emit('get-structure', true)
    },
    dialogSubmit(event) {
      this.loadingText = 'Applying changes...'
      this.loading = true
      let query = 'ALTER TABLE `' + this.sidebarSelected[0]['name'] + '`'

      if (['new','edit'].includes(this.dialogOptions.mode)) {
        // Parse Form Fields
        if (!['CHAR','VARCHAR','TEXT','TINYTEXT','MEDIUMTEXT','LONGTEXT','ENUM','SET'].includes(this.dialogOptions.item.type)) {
          this.dialogOptions.item.encoding = ''
          this.dialogOptions.item.collation = ''
        }
        if (!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT','DECIMAL','FLOAT','DOUBLE'].includes(this.dialogOptions.item.type)) this.dialogOptions.item.unsigned = false
        if (!['DATETIME','TIMESTAMP'].includes(this.dialogOptions.item.type)) this.dialogOptions.item.current_timestamp = false
        if (!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT'].includes(this.dialogOptions.item.type)) this.dialogOptions.item.auto_increment = false

        // Check if all fields are filled
        if (!this.$refs.dialogForm.validate()) {
          EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
          this.loading = false
          return
        }

        // Build Query
        if (this.dialogOptions.mode == 'new') query += ' ADD `' + this.dialogOptions.item.name + '`'
        else if (this.dialogOptions.mode == 'edit') query += ' CHANGE `' + this.gridApi.structure.columns.getSelectedRows()[0].Name  + '` `' + this.dialogOptions.item.name + '`'
        query += ' ' + this.dialogOptions.item.type 
          + (this.dialogOptions.item.length.length > 0 ? (this.dialogOptions.item.length.indexOf(',') == -1) ? '(' + this.dialogOptions.item.length + ')' : '(' + this.dialogOptions.item.length.split(",").map(item => "'" + item.trim() + "'") + ')' : '')
          + (this.dialogOptions.item.unsigned ? ' UNSIGNED' : '')
          + (this.dialogOptions.item.collation.length > 0 ? ' CHARACTER SET ' + this.dialogOptions.item.encoding + ' COLLATE ' + this.dialogOptions.item.collation : '')
          + (this.dialogOptions.item.null ? ' NULL' : ' NOT NULL')
          + (this.dialogOptions.item.default.length > 0 ? " DEFAULT" + (this.dialogOptions.item.default == 'CURRENT_TIMESTAMP' ? ' CURRENT_TIMESTAMP' : " '" + this.dialogOptions.item.default + "'") : '')
          + (this.dialogOptions.item.current_timestamp ? ' ON UPDATE CURRENT_TIMESTAMP' : '')
          + (this.dialogOptions.item.auto_increment ? ' AUTO_INCREMENT' : '')
          + (this.dialogOptions.item.comment ? " COMMENT '" + this.dialogOptions.item.comment + "'" : '')
      }
      else if (this.dialogOptions.mode == 'delete') query += ' DROP COLUMN `' + this.gridApi.structure.columns.getSelectedRows()[0]['Name'] + '`'
      else if (this.dialogOptions.mode == 'drag') {
        query += ' MODIFY ' + this.gridApi.structure.columns.getDisplayedRowAtIndex(event.node.rowIndex).data['Name']
          + ' ' + event.node.data['Type'] 
          + (event.node.data['Length'] !== null ? '(' + event.node.data['Length'] + ')' : '')
          + (event.node.data['Unsigned'] ? ' UNSIGNED' : '')
          + (event.node.data['Collation'] !== null ? ' CHARACTER SET ' + event.node.data['Encoding'] + ' COLLATE ' + event.node.data['Collation'] : '')
          + (event.node.data['Allow NULL'] ? ' NULL' : ' NOT NULL')
          + (event.node.data['Default'] !== null ? " DEFAULT" + (event.node.data['Default'] == 'CURRENT_TIMESTAMP' ? ' CURRENT_TIMESTAMP' : " '" + event.node.data['Default'] + "'") : '')
          + (event.node.data['Extra'].toLowerCase() == 'on update current_timestamp' ? ' ON UPDATE CURRENT_TIMESTAMP' : '')
          + (event.node.data['Extra'].toLowerCase() ==  'auto_increment' ? ' AUTO_INCREMENT' : '')
          + (event.node.data['Comment'] ? " COMMENT '" + event.node.data['Comment'] + "'" : '')
          + (event.node.rowIndex == 0 ? ' FIRST' : (' AFTER `' + this.gridApi.structure.columns.getDisplayedRowAtIndex(event.node.rowIndex - 1).data['Name']) + '`')
      }
      query += ';'

      // Execute query
      this.execute(query)
    },
    execute(query) {
      let promise = new Promise((resolve, reject) => {
        EventBus.$emit('execute-structure', query, this.dialogOptions.mode == 'drag', resolve, reject)
      })
      promise.then(() => { this.dialog = false })
        .catch(() => { if (this.dialogOptions.mode == 'delete') this.dialog = false })
        .finally(() => { this.loading = false })
    },
    dialogCancel() {
      if (this.loading) {
        this.loadingText = 'Interrupting changes...'
        this.loading2 = true
        new Promise((resolve, reject) => {
          EventBus.$emit('stop-structure', resolve, reject)
        }).finally(() => { 
          this.loading2 = false
          this.dialog = false
        })
      }
      else this.dialog = false
    },
  }
}
</script>