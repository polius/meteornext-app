<template>
  <div style="height:100%">
    <!--------->
    <!-- FKs -->
    <!--------->
    <div style="height:calc(100% - 84px)">
      <ag-grid-vue ref="agGridStructureFKs" @grid-ready="onGridReady" @new-columns-loaded="onNewColumnsLoaded" @cell-key-down="onCellKeyDown" @row-double-clicked="onRowDoubleClicked" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowDragManaged="true" suppressMoveWhenRowDragging="true" rowHeight="35" headerHeight="35" rowSelection="single" rowDeselection="true" stopEditingWhenGridLosesFocus="true" :columnDefs="structureHeaders.fks" :rowData="structureItems.fks"></ag-grid-vue>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn @click="addFK" text small title="New Foreign Key" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn :disabled="structureItems.fks.length == 0" @click="removeFK" text small title="Remove Foreign Key" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="refreshFKs" text small title="Refresh Foreign Keys" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            <v-icon v-if="bottomBar.structure.fks['status'] == 'success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:5px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBar.structure.fks['status'] == 'failure'" title="Failed" small style="color:rgb(231, 76, 60); padding-bottom:1px; padding-right:5px;">fas fa-times-circle</v-icon>
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
                    <v-card>
                      <v-toolbar flat dense height="42" color="#2e3131">
                        <div class="body-1">Table: {{ this.treeviewSelected['name'] }}</div>
                      </v-toolbar>
                      <v-card-text style="padding-bottom:0px;">
                        <v-text-field v-model="dialogOptions.item.name" label="Name" autofocus required style="padding-top:0px;"></v-text-field>
                        <v-select v-model="dialogOptions.item.column" :items="structureColumnsName" :rules="[v => !!v || '']" label="Column" auto-select-first required style="padding-top:0px;"></v-select>
                      </v-card-text>
                    </v-card>
                    <v-card style="margin-top:10px;">
                      <v-toolbar flat dense height="42" color="#2e3131">
                        <div class="body-1">References</div>
                      </v-toolbar>
                      <v-card-text style="padding-bottom:0px;">
                        <v-select v-model="dialogOptions.item.fk_table" :items="tableItems" :rules="[v => !!v || '']" label="Table" auto-select-first required style="padding-top:0px;"></v-select>
                        <v-text-field v-model="dialogOptions.item.fk_column" label="Column" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                      </v-card-text>
                    </v-card>
                    <v-card style="margin-top:10px;">
                      <v-toolbar flat dense height="42" color="#2e3131">
                        <div class="body-1">Action</div>
                      </v-toolbar>
                      <v-card-text style="padding-bottom:0px;">
                        <v-select v-model="dialogOptions.item.on_update" :items="server.fkRules" :rules="[v => !!v || '']" label="On update" auto-select-first required style="padding-top:0px;"></v-select>
                        <v-select v-model="dialogOptions.item.on_delete" :items="server.fkRules" :rules="[v => !!v || '']" label="On delete" auto-select-first required style="padding-top:0px;"></v-select>
                      </v-card-text>
                    </v-card>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col v-if="dialogOptions.submit.length > 0" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="dialogSubmit" color="primary">{{ dialogOptions.submit }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogOptions.cancel.length > 0" style="margin-bottom:10px;">
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
      dialogOptions: { mode: '', title: '', text: '', item: {}, submit: '', cancel: '' }
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'gridApi',
      'columnApi',
      'structureHeaders',
      'structureItems',
      'structureColumnsName',
      'treeviewSelected',
      'server',
      'tableItems',
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
        if (val == 'fks') this.resizeTable()
      })
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
      }
    },
    resizeTable() {
      var allColumnIds = [];
      this.columnApi.structure.fks.getAllColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi.structure.fks.autoSizeColumns(allColumnIds);
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
    addFK() {
      this.dialogOptions = {
        mode: 'new',
        title: 'New Foreign Key',
        text: '',
        item: { name: '', column: '', fk_table: '', fk_column: '', on_update: '', on_delete: '' },
        submit: 'Save',
        cancel: 'Cancel'
      }
      this.dialog = true
    },
    removeFK() {
      this.dialogOptions = {
        mode: 'delete',
        title: 'Delete foreign key?',
        text: "Are you sure you want to delete the foreign key '" + this.gridApi.structure.fks.getSelectedRows()[0].Name + "' from this table? This action cannot be undone.",
        item: {},
        submit: 'Delete',
        cancel: 'Cancel'
      }
      this.dialog = true
    },
    refreshFKs() {
      EventBus.$emit('GET_STRUCTURE')
    },
    dialogSubmit() {
      this.loading = true
      let query = ''
      if (this.dialogOptions.mode == 'new') {
        // Check if all fields are filled
        if (!this.$refs.dialogForm.validate()) {
          EventBus.$emit('SEND_NOTIFICATION', 'Please make sure all required fields are filled out correctly', 'error')
          this.loading = false
          return
        }
        // Build query
        let constraintName = (this.dialogOptions.item.name.length > 0) ? 'CONSTRAINT ' + this.dialogOptions.item.name : ''
        query = "ALTER TABLE " + this.treeviewSelected['name'] + " ADD " + constraintName + " FOREIGN KEY(" + this.dialogOptions.item.column + ") REFERENCES " + this.dialogOptions.item.fk_table + "(" + this.dialogOptions.item.fk_column + ") ON UPDATE " + this.dialogOptions.item.on_update + " ON DELETE " + this.dialogOptions.item.on_delete + ";"
      }
      else if (this.dialogOptions.mode == 'delete') {
        let row = this.gridApi.structure.fks.getSelectedRows()[0]
        query = "ALTER TABLE " + this.treeviewSelected['name'] + " DROP FOREIGN KEY " + row.Name + ";"
      }
      // Execute query
      this.execute(query)
    },
    execute(query) {
      let promise = new Promise((resolve, reject) => {
        EventBus.$emit('EXECUTE_STRUCTURE', query, resolve, reject)
      })
      promise.then(() => { this.dialog = false })
        .catch(() => { if (this.dialogOptions.mode == 'delete') this.dialog = false })
        .finally(() => { this.loading = false })
    },
  }
}
</script>