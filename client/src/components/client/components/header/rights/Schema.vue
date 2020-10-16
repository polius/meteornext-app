<template>
  <div style="height:100%">
    <div style="height: calc(100% - 84px)">
      <ag-grid-vue suppressDragLeaveHidesColumns suppressContextMenu suppressColumnVirtualisation @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" @cell-clicked="onCellClicked" @row-double-clicked="onRowDoubleClicked" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" rowDeselection="true" :columnDefs="header" :rowData="schema"></ag-grid-vue>
    </div>
    <v-row no-gutters style="height:35px; border-top:2px solid #3b3b3b; width:100%">
      <v-btn @click="addRights" text small title="Grant Rights" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="!selectedRows" @click="removeRights" text small title="Revoke Rights" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
    </v-row>
    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="dialog" persistent max-width="60%">
      <v-card>
        <v-toolbar v-if="dialogOptions.mode != 'delete'" flat color="primary">
          <v-toolbar-title class="white--text">{{ dialogOptions.title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div v-if="dialogOptions.mode == 'delete'" class="text-h6" style="font-weight:400;">{{ dialogOptions.title }}</div>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <div v-if="dialogOptions.text.length > 0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogOptions.text }}</div>
                  <div v-if="Object.keys(dialogOptions.item).length > 0">
                    <v-select v-model="dialogOptions.item.type" @change="onChangeType" :items="['Database','Table','Column']" :rules="[v => !!v || '']" label="Type" auto-select-first required style="padding-top:0px;"></v-select>
                    <v-row no-gutters>
                      <v-col><v-text-field v-model="dialogOptions.item.database" :rules="[v => !!v || '']" label="Database" required style="padding-top:0px;"></v-text-field></v-col>
                      <v-col v-if="['Table','Column'].includes(dialogOptions.item.type)" style="margin-left:10px"><v-text-field v-model="dialogOptions.item.table" :rules="[v => !!v || '']" label="Table" required style="padding-top:0px;"></v-text-field></v-col>
                      <v-col v-if="dialogOptions.item.type == 'Column'" style="margin-left:10px;"><v-text-field v-model="dialogOptions.item.column" :rules="[v => !!v || '']" label="Column" required style="padding-top:0px;"></v-text-field></v-col>
                    </v-row>
                    <v-row no-gutters>
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
                            <v-checkbox :disabled="dialogOptions.item.type != 'Database'" v-model="dialogOptions.item.rights.create_tmp_table" dense label="Create Temporary Table" hide-details style="margin:0px;"></v-checkbox>
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
                      <v-btn :loading="loading" @click="dialogSubmit" color="primary">{{ dialogOptions.submit }}</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialog = false" outlined color="#e74d3c">{{ dialogOptions.cancel }}</v-btn>
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
      'rightsItem',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('reload-rights', this.reloadRights);
  },
  watch: {
    schema: {
      handler() {
        let change = JSON.stringify(this.rights['schema']) !== JSON.stringify(this.schema)
        console.log("change: " + change.toString())
      },
      deep: true
    },
    tab(value) {
      if (value == 2) this.resizeTable()
    }
  },
  methods: {
    reloadRights() {
      this.schema = JSON.parse(JSON.stringify(this.rights['schema']))
    },
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
      // this.resizeTable()
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
        navigator.clipboard.writeText(e.value)

        // Highlight cells
        e.event.target.classList.add('ag-cell-highlight');
        e.event.target.classList.remove('ag-cell-highlight-animation')

        // Add animation
        window.setTimeout(function () {
            e.event.target.classList.remove('ag-cell-highlight')
            e.event.target.classList.add('ag-cell-highlight-animation')
            e.event.target.style.transition = "background-color " + 200 + "ms"

            // Remove animation
            window.setTimeout(function () {
                e.event.target.classList.remove('ag-cell-highlight-animation')
                e.event.target.style.transition = null;
            }, 200);
        }, 200);
      }
    },
    onCellClicked() {
      this.selectedRows = this.gridApi.getSelectedRows().length != 0
    },
    onRowDoubleClicked(event) {
      this.editRights(event.data, event.rowIndex)
    },
    onChangeType() {

    },
    addRights() {
      this.dialogOptions = {
        mode: 'new',
        index: -1,
        title: 'Grant Rights',
        text: '',
        item: { type: 'Database', database: '', table: '', column: '', rights: {} },
        submit: 'Save',
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
        title: 'Edit Rights',
        text: '',
        item: {
          type: data['type'].charAt(0).toUpperCase() + data['type'].slice(1), 
          database: data['schema'].split('.')[0], 
          table: ['table','column'].includes(data['type']) ? data['schema'].split('.')[1] : '',
          column: data['type'] == 'column' ? data['schema'].split('.')[2] : '',
          rights,
        },
        submit: 'Save',
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
        submit: 'Delete',
        cancel: 'Cancel'
      }
      this.dialog = true
    },
    dialogSubmit() {     
      // Check constraints
      if (['new','edit'].includes(this.dialogOptions.mode)) {
        let validated = true
        this.gridApi.forEachNode((node) => {
          if (node.rowIndex != this.dialogOptions.index && node.data['type'] == this.dialogOptions.item.type.toLowerCase() && node.data['schema'] == this.getSchema()) {
            EventBus.$emit('send-notification', 'This right type + schema currently exists in the table.', 'error')
            validated = false
            return
          }
        })
        if (!validated) return
      }
      // Add element
      if (this.dialogOptions.mode == 'new') {
        this.gridApi.applyTransaction({ add: [this.getItem()] })
      }
      // Update element
      else if (this.dialogOptions.mode == 'edit') {
        let item = this.getItem()
        this.currentItem.type = item.type
        this.currentItem.schema = item.schema
        this.currentItem.rights = item.rights
        this.gridApi.applyTransaction({ update: [this.currentItem] })
      }
      // Remove element
      else if (this.dialogOptions.mode == 'delete') {
        let selectedData = this.gridApi.getSelectedRows();
        this.gridApi.applyTransaction({ remove: selectedData })
        this.selectedRows = false
      }
      // Get diff
      this.getDiff()
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
    getDiff() {
      let diff = { add: [], remove: [], update: [] }
      // Diff between this.rights['schema'] and this.schema: (add | update | remove) and build SQL stmts
      console.log(this.rights['schema'])
      console.log(this.schema)

      // add
      // for (let i of this.schema) {
      //   let found = this.rights['schema'].find(x => x.type == i.type && x.schema == i.schema && )
      // }
      // remove

      // update
      // newData.find(x => x.investor === investor)

      console.log(diff)

    }
  }
}
</script>