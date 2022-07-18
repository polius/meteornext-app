<template>
  <div style="height:100%">
    <!--------->
    <!-- FKs -->
    <!--------->
    <div style="height:calc(100% - 84px)">
      <ag-grid-vue ref="agGridStructureFKs" suppressDragLeaveHidesColumns suppressFieldDotNotation suppressContextMenu preventDefaultOnContextMenu oncontextmenu="return false" @grid-ready="onGridReady" @new-columns-loaded="onNewColumnsLoaded" @cell-key-down="onCellKeyDown" @cell-clicked="onCellClicked" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowDragManaged="true" suppressMoveWhenRowDragging="true" rowHeight="35" headerHeight="35" rowSelection="single" rowDeselection="true" stopEditingWhenCellsLoseFocus="true" :columnDefs="structureHeaders.fks" :rowData="structureItems.fks"></ag-grid-vue>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn @click="refreshFKs" text small title="Refresh Foreign Keys" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="addFK" text small title="New Foreign Key" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn :disabled="!selectedRows" @click="removeFK" text small title="Remove Foreign Key" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            <v-icon v-if="bottomBar.structure.fks['status'] == 'success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:7px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBar.structure.fks['status'] == 'failure'" title="Failed" small style="color:#EF5354; padding-bottom:1px; padding-right:7px;">fas fa-times-circle</v-icon>
            <span :title="bottomBar.structure.fks['text']">{{ bottomBar.structure.fks['text'] }}</span>
          </div>
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBar.structure.fks['info'] }}</div>
        </v-col>
      </v-row>
    </div>
    <!------------>
    <!-- DIALOG -->
    <!------------>
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
                <v-form ref="dialogForm" style="margin-top:15px; margin-bottom:15px">
                  <div v-if="Object.keys(dialogOptions.item).length > 0">
                    <v-text-field v-model="dialogOptions.item.name" label="Name" autofocus required style="padding-top:0px;"></v-text-field>
                    <v-text-field readonly v-model="dialogOptions.item.table" label="Table" required style="padding-top:0px;"></v-text-field>
                    <v-select v-model="dialogOptions.item.column" :items="dialogOptions.item.column_items" :rules="[v => !!v || '']" item-value="column_name" label="Column" return-object required style="padding-top:0px;">
                      <template v-slot:[`selection`]="{ item }">
                        {{ item.column_name + ' ' + item.column_type }}
                      </template>
                      <template v-slot:[`item`]="{ item }">
                        {{ item.column_name + ' ' + item.column_type }}
                      </template>
                    </v-select>
                    <v-select @change="getColumns(dialogOptions.item.fk_table, true)" v-model="dialogOptions.item.fk_table" :items="tableItems" :rules="[v => !!v || '']" label="Target table" required style="padding-top:0px;"></v-select>
                    <v-select v-model="dialogOptions.item.fk_column" :items="dialogOptions.item.fk_column_items" item-value="column_name" :rules="[v => !!v || '']" label="Target column" return-object required style="padding-top:0px;">
                      <template v-slot:[`selection`]="{ item }">
                        {{ item.column_name + ' ' + item.column_type }}
                      </template>
                      <template v-slot:[`item`]="{ item }">
                        {{ item.column_name + ' ' + item.column_type }}
                      </template>
                    </v-select>
                    <v-select v-model="dialogOptions.item.on_delete" :items="server.fkRules" label="ON DELETE" style="padding-top:0px;"></v-select>
                    <v-select v-model="dialogOptions.item.on_update" :items="server.fkRules" label="ON UPDATE" hide-details style="padding-top:0px;"></v-select>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col v-if="dialogOptions.submit.length > 0" cols="auto" style="margin-right:5px">
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
      'index',
      'id',
      'structureHeaders',
      'structureItems',
      'sidebarSelected',
      'server',
      'database',
      'tableItems',
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
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
      if (this.dialogOptions.item.column_items.length == 0) this.getColumns(this.sidebarSelected[0]['name'])
    },
    headerTabSelected(val) {
      if (val == 'structure') {
        this.$nextTick(() => {
          if (this.gridApi.structure.fks != null) this.resizeTable()
        })
      }
    },
    tabStructureSelected(val) {
      if (val == 'fks') {
        this.$nextTick(() => { this.resizeTable() })
      }
    },
    "structureItems.fks" () {
      this.selectedRows = false
    }
  },
  methods: {
    onGridReady(params) {
      this.gridApi.structure.fks = params.api
      this.columnApi.structure.fks = params.columnApi
      this.$refs['agGridStructureFKs'].$el.addEventListener('click', this.onGridClick)
      this.gridApi.structure.fks.showLoadingOverlay()
    },
    onNewColumnsLoaded() {
      if (this.gridApi.structure.fks != null) this.resizeTable()
    },
    onGridClick(event) {
      if (event.target.className == 'ag-center-cols-viewport') {
        this.gridApi.structure.fks.deselectAll()
        this.selectedRows = false
      }
    },
    resizeTable() {
      var allColumnIds = [];
      this.columnApi.structure.fks.getColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi.structure.fks.autoSizeColumns(allColumnIds);
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        let selectedRows = this.gridApi.structure.fks.getSelectedRows()
        if (selectedRows.length > 1) {
          // Copy values
          let header = Object.keys(selectedRows[0])
          let value = selectedRows.map(row => header.map(fieldName => row[fieldName] == null ? 'NULL' : row[fieldName]).join('\t')).join('\n')
          navigator.clipboard.writeText(value)
          // Apply effect
          // this.gridApi.structure.fks.flashCells({
          //   rowNodes: this.gridApi.structure.fks.getSelectedNodes(),
          //   flashDelay: 200,
          //   fadeDelay: 200,
          // })
        }
        else {
          // Copy value
          navigator.clipboard.writeText(e.value)
          // Apply effect
          this.gridApi.structure.fks.flashCells({
            rowNodes: this.gridApi.structure.fks.getSelectedNodes(),
            columns: [this.gridApi.structure.fks.getFocusedCell().column.colId],
            flashDelay: 200,
            fadeDelay: 200,
          })
        }
      }
      else if (['ArrowUp','ArrowDown'].includes(e.event.key)) {
        let cell = this.gridApi.structure.fks.getFocusedCell()
        let row = this.gridApi.structure.fks.getDisplayedRowAtIndex(cell.rowIndex)
        let node = this.gridApi.structure.fks.getRowNode(row.id)
        this.gridApi.structure.fks.deselectAll()
        node.setSelected(true)
      }
    },
    onCellClicked() {
      this.selectedRows = this.gridApi.structure.fks.getSelectedRows().length != 0
    },
    addFK() {
      this.dialogOptions = {
        mode: 'new',
        icon: 'fas fa-plus',
        title: 'NEW FOREIGN KEY',
        text: '',
        item: { name: '', table: this.sidebarSelected[0]['name'], column_items: [], column: '', fk_table: '', fk_column_items: [], fk_column: '', on_update: '', on_delete: '' },
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialog = true
    },
    removeFK() {
      this.dialogOptions = {
        mode: 'delete',
        icon: 'fas fa-minus',
        title: 'DELETE FOREIGN KEY',
        text: "Are you sure you want to delete the foreign key '" + this.gridApi.structure.fks.getSelectedRows()[0].Name + "' from this table? This action cannot be undone.",
        item: {},
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialog = true
    },
    refreshFKs() {
      EventBus.$emit('get-structure', true)
    },
    dialogSubmit() {
      this.loadingText = 'Applying changes...'
      this.loading = true
      let query = ''
      if (this.dialogOptions.mode == 'new') {
        // Check if all fields are filled
        if (!this.$refs.dialogForm.validate()) {
          EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
          this.loading = false
          return
        }
        // Build query
        let constraintName = (this.dialogOptions.item.name.length > 0) ? 'CONSTRAINT `' + this.dialogOptions.item.name + '`' : ''
        query = "ALTER TABLE `" + this.sidebarSelected[0]['name'] + "` ADD " + constraintName + " FOREIGN KEY (" + this.dialogOptions.item.column.column_name + ") REFERENCES " + this.dialogOptions.item.fk_table + "(" + this.dialogOptions.item.fk_column.column_name + ")"
        if (this.dialogOptions.item.on_delete.length > 0) query += " ON DELETE " + this.dialogOptions.item.on_delete
        if (this.dialogOptions.item.on_update.length > 0) query += " ON UPDATE " + this.dialogOptions.item.on_update
        query += ';'
      }
      else if (this.dialogOptions.mode == 'delete') {
        let row = this.gridApi.structure.fks.getSelectedRows()[0]
        query = "ALTER TABLE `" + this.sidebarSelected[0]['name'] + "` DROP FOREIGN KEY `" + row.Name + "`;"
      }
      // Execute query
      this.execute(query)
    },
    execute(query) {
      let promise = new Promise((resolve, reject) => {
        EventBus.$emit('execute-structure', query, false, resolve, reject)
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
    getColumns(table, target=false) {
      if (target) {
        this.dialogOptions.item.fk_column_items = []
        this.dialogOptions.item.fk_column = ''
        this.$refs.dialogForm.resetValidation()
      } else {
        this.dialogOptions.item.column_items = []
        this.dialogOptions.item.column = ''
      }
      const payload = {
        connection: this.id + '-shared',
        server: this.server.id,
        database: this.database,
        table: table
      }
      axios.get('/client/structure/columns', { params: payload })
        .then((response) => {
          let data = JSON.parse(response.data.columns)
          if (target) this.dialogOptions.item.fk_column_items = data
          else this.dialogOptions.item.column_items = data
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
  }
}
</script>