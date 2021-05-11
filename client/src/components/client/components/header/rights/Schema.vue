<template>
  <div style="height:100%">
    <div style="height: calc(100% - 84px)">
      <ag-grid-vue suppressDragLeaveHidesColumns suppressContextMenu preventDefaultOnContextMenu suppressColumnVirtualisation @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" @cell-clicked="onCellClicked" @row-double-clicked="onRowDoubleClicked" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" rowDeselection="true" :columnDefs="header" :rowData="schema"></ag-grid-vue>
    </div>
    <v-row no-gutters style="height:35px; border-top:2px solid #3b3b3b; width:100%">
      <v-btn :disabled="disabled" @click="addRights" text small title="Grant Rights" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="disabled || !selectedRows" @click="removeRights" text small title="Revoke Rights" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
    </v-row>
    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="dialog" max-width="60%">
      <v-card>
        <v-toolbar v-if="dialogOptions.mode != 'delete'" dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">{{ dialogOptions.title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div v-if="dialogOptions.mode == 'delete'" class="text-h6" style="font-weight:400;">{{ dialogOptions.title }}</div>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <div v-if="dialogOptions.text.length > 0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogOptions.text }}</div>
                  <div v-if="Object.keys(dialogOptions.item).length > 0">
                    <v-select v-model="dialogOptions.item.type" :items="['Database','Table','Column']" :rules="[v => !!v || '']" label="Type" auto-select-first required style="padding-top:0px;"></v-select>
                    <v-form ref="form" @submit.prevent>
                      <v-row no-gutters>
                        <v-col><v-text-field v-model="dialogOptions.item.database" :rules="[v => !!v || '']" label="Database" hint="Wildcards allowed: % _" required style="padding-top:0px;"></v-text-field></v-col>
                        <v-col v-if="['Table','Column'].includes(dialogOptions.item.type)" style="margin-left:10px"><v-text-field v-model="dialogOptions.item.table" :rules="[v => !!v || '']" label="Table" required style="padding-top:0px;"></v-text-field></v-col>
                        <v-col v-if="dialogOptions.item.type == 'Column'" style="margin-left:10px;"><v-text-field v-model="dialogOptions.item.column" :rules="[v => !!v || '']" label="Column" required style="padding-top:0px;"></v-text-field></v-col>
                      </v-row>
                    </v-form>
                    <v-row no-gutters style="margin-top:10px">
                      <v-col style="margin-right:15px;">
                        <div class="body-2" style="margin-bottom:5px;">Database</div>
                        <v-card>
                          <v-card-text style="padding:10px; padding-bottom:15px">
                            <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.create" dense label="Create" hide-details style="margin:0px;"></v-checkbox>
                            <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.drop" dense label="Drop" hide-details style="margin:0px;"></v-checkbox>
                            <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.alter" dense label="Alter" hide-details style="margin:0px;"></v-checkbox>
                            <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.index" dense label="Index" hide-details style="margin:0px;"></v-checkbox>
                            <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.trigger" dense label="Trigger" hide-details style="margin:0px;"></v-checkbox>
                            <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.event" dense label="Event" hide-details style="margin:0px;"></v-checkbox>
                            <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.references" dense label="References" hide-details style="margin:0px;"></v-checkbox>
                            <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.create_temporary_tables" dense label="Create Temporary Tables" hide-details style="margin:0px;"></v-checkbox>
                            <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.lock_tables" dense label="Lock Tables" hide-details style="margin:0px;"></v-checkbox>
                          </v-card-text>
                        </v-card>
                      </v-col>
                      <v-col style="margin-right:15px;">
                        <v-col style="padding:0px;">
                          <div class="body-2" style="margin-bottom:5px;">Tables</div>
                          <v-card>
                            <v-card-text style="padding:10px; padding-bottom:15px">
                              <v-checkbox v-model="dialogOptions.item.rights.select" dense label="Select" hide-details style="margin:0px;"></v-checkbox>
                              <v-checkbox v-model="dialogOptions.item.rights.insert" dense label="Insert" hide-details style="margin:0px;"></v-checkbox>
                              <v-checkbox v-model="dialogOptions.item.rights.update" dense label="Update" hide-details style="margin:0px;"></v-checkbox>
                              <v-checkbox :disabled="dialogOptions.item.type == 'Column'" v-model="dialogOptions.item.rights.delete" dense label="Delete" hide-details style="margin:0px;"></v-checkbox>
                            </v-card-text>
                          </v-card>
                        </v-col>
                        <v-col style="padding:0px; margin-top:10px">
                          <div class="body-2" style="margin-bottom:5px;">Views</div>
                          <v-card>
                            <v-card-text style="padding:10px; padding-bottom:15px">
                              <v-checkbox :disabled="dialogOptions.item.type == 'Column'" v-model="dialogOptions.item.rights.show_view" dense label="Show View" hide-details style="margin:0px;"></v-checkbox>
                              <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.create_view" dense label="Create View" hide-details style="margin:0px;"></v-checkbox>
                            </v-card-text>
                          </v-card>
                        </v-col>
                      </v-col>
                      <v-col style="padding:0px;">
                        <div class="body-2" style="margin-bottom:5px;">Routines</div>
                        <v-card>
                          <v-card-text style="padding:10px; padding-bottom:15px">
                            <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.create_routine" dense label="Create Routine" hide-details style="margin:0px;"></v-checkbox>
                            <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.alter_routine" dense label="Alter Routine" hide-details style="margin:0px;"></v-checkbox>
                            <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.execute" dense label="Execute" hide-details style="margin:0px;"></v-checkbox>
                          </v-card-text>
                        </v-card>
                      </v-col>
                    </v-row>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="dialogSubmit" color="#00b16a">{{ dialogOptions.submit }}</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialog = false" color="error">{{ dialogOptions.cancel }}</v-btn>
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

<style scoped src="@/styles/agGridVue.css"></style>

<script>
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'
import {AgGridVue} from "ag-grid-vue";

export default {
  data() {
    return {
      mode: '',
      disabled: true,
      // AG Grid
      gridApi: null,
      columnApi: null,
      header: [
        { headerName: 'Type', colId: 'type', field: 'type', sortable: true, filter: true, resizable: true, editable: false, 
          cellRenderer: function(params) {
            if (params.value == 'database') return '<i class="fas fa-database" title="Database" style="color:#ec644b; margin-right:10px"></i>Database';
            else if (params.value == 'table') return '<i class="fas fa-bars" title="Table" style="color:#F29111; margin-right:10px"></i>Table';
            else if (params.value == 'column') return '<i class="fas fa-grip-vertical" title="Column" style="color:#f2d984; margin-right:10px"></i>Column';
          }
        },
        { headerName: 'Schema', colId: 'schema', field: 'schema', sortable: true, filter: true, resizable: true, editable: false },
        { headerName: 'Rights', colId: 'rights', field: 'rights', sortable: true, filter: true, resizable: true, editable: false,
          valueGetter: function(params) {
            return params.data.rights.map((value) => { return value.charAt(0).toUpperCase() + value.slice(1).replaceAll('_', ' ') }).join(', ')
          }
        }
      ],
      schema: [],
      // Dialog
      dialog: false,
      dialogOptions: { mode: '', title: '', text: '', item: {}, submit: '', cancel: '' },
      currentItem: {},
      // AG Grid
      selectedRows: false,
      // Loading
      loading: false,
    }
  },
  props: { tab: Number },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'rights',
      'rightsDiff',
      'rightsSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('reload-rights', this.reloadRights);
  },
  watch: {
    rightsSelected: function(val) {
      this.disabled = (Object.keys(val).length == 0 && this.mode == 'edit') ? true : false
    },
    dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
      })
    },
    tab(value) {
      if (value == 2) this.resizeTable()
    }
  },
  methods: {
    reloadRights(mode) {
      this.mode = mode
      this.schema = JSON.parse(JSON.stringify(this.rights['schema']))
      if (mode == 'clone') {
        this.rights['schema'] = []
        this.computeDiff()
      }
    },
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
    },
    resizeTable() {
      this.$nextTick(() => {
        if (this.gridApi != null) {
          if (this.rights['schema'].length == 0) this.gridApi.sizeColumnsToFit()
          else {
            let allColIds = this.columnApi.getAllColumns().map(column => column.colId)
            this.columnApi.autoSizeColumns(allColIds)
          }
        }
      })
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        // Copy value
        navigator.clipboard.writeText(e.value)
        // Apply effect
        this.gridApi.flashCells({
          rowNodes: this.gridApi.getSelectedNodes(),
          columns: [this.gridApi.getFocusedCell().column.colId],
          flashDelay: 200,
          fadeDelay: 200,
        })
      }
      else if (e.event.key == "Enter") this.editRights(e.data, e.rowIndex)
      else if (['ArrowUp','ArrowDown'].includes(e.event.key)) {
        let cell = this.gridApi.getFocusedCell()
        let row = this.gridApi.getDisplayedRowAtIndex(cell.rowIndex)
        let node = this.gridApi.getRowNode(row.id)
        this.gridApi.deselectAll()
        node.setSelected(true)
      }
    },
    onCellClicked() {
      this.selectedRows = this.gridApi.getSelectedRows().length != 0
    },
    onRowDoubleClicked(event) {
      this.editRights(event.data, event.rowIndex)
    },
    addRights() {
      this.dialogOptions = {
        mode: 'new',
        index: -1,
        title: 'GRANT RIGHTS',
        text: '',
        item: { type: 'Database', database: '', table: '', column: '', rights: {} },
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialog = true
    },
    editRights(data, index) {
      // Build rights
      let rights = {}
      data['rights'].forEach((item) => { rights[item] = true })
      // Build dialogOptions
      this.dialogOptions = {
        mode: 'edit',
        index,
        title: 'EDIT RIGHTS',
        text: '',
        item: {
          type: data['type'].charAt(0).toUpperCase() + data['type'].slice(1), 
          database: data['schema'].split('.')[0], 
          table: ['table','column'].includes(data['type']) ? data['schema'].split('.')[1] : '',
          column: data['type'] == 'column' ? data['schema'].split('.')[2] : '',
          rights,
        },
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      // Store item
      this.currentItem = data
      this.dialog = true
    },
    removeRights() {
      this.dialogOptions = {
        mode: 'delete',
        title: 'Revoke rights?',
        text: "Are you sure you want remove the selected rights? This action cannot be undone.",
        item: {},
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialog = true
    },
    dialogSubmit() {    
      let item = null 
      // Check constraints
      if (['new','edit'].includes(this.dialogOptions.mode)) {
        // Check unique (rightType, rightSchema)
        let error = false
        this.gridApi.forEachNode((node) => {
          if (node.rowIndex != this.dialogOptions.index && node.data['type'] == this.dialogOptions.item.type.toLowerCase() && node.data['schema'] == this.getSchema()) {
            error = true
            return
          }
        })
        if (error) {
          EventBus.$emit('send-notification', 'This schema currently exists', 'error')
          return
        }
        // Retrieve current item
        item = this.getItem()
        // Check if all fields are filled
        if (!this.$refs.form.validate()) {
          EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', 'error')
          return
        }
        // Check if some right is selected
        if (item.rights.length == 0) {
          EventBus.$emit('send-notification', 'Please select at least one right', 'error')
          return
        }
      }
      // Add element
      if (this.dialogOptions.mode == 'new') {
        this.schema.push(item)
        this.gridApi.applyTransaction({ add: [item] })
      }
      // Update element
      else if (this.dialogOptions.mode == 'edit') {
        const index = this.schema.findIndex((x) => x['type'] == this.currentItem.type && x['schema'] == this.currentItem.schema)
        this.schema[index] = JSON.parse(JSON.stringify(item))
        this.currentItem.type = item.type
        this.currentItem.schema = item.schema
        this.currentItem.rights = item.rights
        this.gridApi.applyTransaction({ update: [this.currentItem] })
      }
      // Remove element
      else if (this.dialogOptions.mode == 'delete') {
        let selectedData = this.gridApi.getSelectedRows()[0]
        const index = this.schema.findIndex((x) => x['type'] == selectedData.type && x['schema'] == selectedData.schema && JSON.stringify(x['rights']) == JSON.stringify(selectedData.rights))
        this.schema.splice(index, 1);
        this.selectedRows = false
      }
      // Get diff
      this.computeDiff()
      // Close dialog
      this.dialog = false
    },
    getItem() {
      var item = { 
        type: this.dialogOptions.item.type.toLowerCase(),
        schema: this.getSchema(),
        rights: ''
      }
      // Parse rights
      let rights = []
      Object.entries(this.dialogOptions.item.rights).forEach(([key, value]) => {
        if (value) rights.push(key)
      })
      item['rights'] = rights
      // Return item
      return item
    },
    getSchema() {
      if (this.dialogOptions.item.type.toLowerCase() == 'database') return this.dialogOptions.item.database
      else if (this.dialogOptions.item.type.toLowerCase() == 'table') return this.dialogOptions.item.database + '.' + this.dialogOptions.item.table
      else if (this.dialogOptions.item.type.toLowerCase() == 'column') return this.dialogOptions.item.database + '.' + this.dialogOptions.item.table + '.' + this.dialogOptions.item.column
    },
    computeDiff() {
      let diff = this.schema.reduce((acc, val) => {
        // Check matching
        let matching = this.rights['schema'].find((val2) => val.type == val2.type && val.schema == val2.schema && JSON.stringify(val.rights) != JSON.stringify(val2.rights))
        if (matching) {
          let rightsGrant = val.rights.filter(x => !matching.rights.includes(x))
          let rightsRevoke = matching.rights.filter(x => !val.rights.includes(x))
          if (rightsGrant.length > 0) acc['grant'].push({type: val.type, schema: val.schema, rights: rightsGrant, old: matching.rights})
          if (rightsRevoke.length > 0) acc['revoke'].push({type: val.type, schema: val.schema, rights: rightsRevoke, old: matching.rights})
          return acc
        }
        // Check added
        let added = !this.rights['schema'].some(val2 => val.type == val2.type && val.schema == val2.schema && JSON.stringify(val.rights) == JSON.stringify(val2.rights))
        if (added) acc['grant'].push(val)
        return acc
      }, {'grant': [], 'revoke': []})

      // Revokes
      let revokes = this.rights['schema'].filter((val) => !this.schema.some((val2) => 
        val.type == val2.type && val.schema == val2.schema
      ))
      diff['revoke'] = diff['revoke'].concat(revokes)
      this.rightsDiff['schema'] = diff
    },
  }
}
</script>