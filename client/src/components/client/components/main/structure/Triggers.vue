<template>
  <div style="height:100%">
    <!-------------->
    <!-- Triggers -->
    <!--------------->
    <div style="height:calc(100% - 84px)">
      <ag-grid-vue ref="agGridStructureTriggers" @grid-ready="onGridReady" @new-columns-loaded="onNewColumnsLoaded" @cell-key-down="onCellKeyDown" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowDragManaged="true" suppressMoveWhenRowDragging="true" rowHeight="35" headerHeight="35" rowSelection="single" rowDeselection="true" stopEditingWhenGridLosesFocus="true" :columnDefs="structureHeaders.triggers" :rowData="structureItems.triggers"></ag-grid-vue>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn @click="addTrigger" text small title="New Trigger" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn :disabled="structureItems.triggers.length == 0" @click="removeTrigger" text small title="Remove Trigger" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="refreshTriggers" text small title="Refresh Triggers" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            <v-icon v-if="bottomBar.structure.triggers['status'] == 'success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:5px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBar.structure.triggers['status'] == 'failure'" title="Failed" small style="color:rgb(231, 76, 60); padding-bottom:1px; padding-right:5px;">fas fa-times-circle</v-icon>
            <span :title="bottomBar.structure.triggers['text']">{{ bottomBar.structure.triggers['text'] }}</span>
          </div>
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBar.structure.triggers['info'] }}</div>
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
                    <v-text-field v-model="dialogOptions.item.name" label="Name" auto-select-first :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                    <v-select v-model="dialogOptions.item.time" :items="['Before','After']" :rules="[v => !!v || '']" label="Action Time" auto-select-first required style="padding-top:0px;"></v-select>
                    <v-select v-model="dialogOptions.item.event" :items="['Insert','Update','Delete']" :rules="[v => !!v || '']" label="Event" auto-select-first required style="padding-top:0px;"></v-select>
                    <div style="margin-left:auto; margin-right:auto; height:40vh; width:100%">
                      <div id="dialogEditor" style="height:100%;"></div>
                    </div>
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
import * as ace from 'ace-builds';
import 'ace-builds/webpack-resolver';
import 'ace-builds/src-noconflict/ext-language_tools';

import { AgGridVue } from "ag-grid-vue";

import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      // Loading
      loading: false,
      // Dialog
      dialog: false,
      dialogOptions: { mode: '', title: '', text: '', item: {}, submit: '', cancel: '' },
      dialogEditor: null
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'structureHeaders',
      'structureItems',
      'treeviewSelected',
      'bottomBar',
      'tabStructureSelected',
    ], { path: 'client/connection' }),
    ...mapFields([
      'gridApi',
      'columnApi',
    ], { path: 'client/components' }),
  },
  watch: {
    dialog (val) {
      if (!val) return
      if (this.dialogEditor == null) this.initEditor()
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
    },
    tabStructureSelected(val) {
      this.$nextTick(() => {
        if (val == 'triggers') this.resizeTable()
      })
    }
  },
  methods: {
    initEditor() {
      this.$nextTick(() => {
        // Editor Settings
        this.dialogEditor = ace.edit("dialogEditor", {
          mode: "ace/mode/sql",
          theme: "ace/theme/monokai",
          fontSize: 14,
          showPrintMargin: false,
          wrap: true,
          autoScrollEditorIntoView: true,
          enableBasicAutocompletion: true,
          enableLiveAutocompletion: true,
          enableSnippets: false,
          highlightActiveLine: false
        });
        this.dialogEditor.session.setOptions({ tabSize: 4, useSoftTabs: false })

        // Add custom keybinds
        this.dialogEditor.container.addEventListener("keydown", (e) => {
          // - Increase Font Size -
          if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault()
            let size = parseInt(this.dialogEditor.getFontSize(), 10) || 12
            this.dialogEditor.setFontSize(size + 1)
          }
          // - Decrease Font Size -
          else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault()
            let size = parseInt(this.dialogEditor.getFontSize(), 10) || 12
            this.dialogEditor.setFontSize(Math.max(size - 1 || 1))
          }
        }, false);
      })
    },
    onGridReady(params) {
      this.gridApi.structure.triggers = params.api
      this.columnApi.structure.triggers = params.columnApi
      this.$refs['agGridStructureTriggers'].$el.addEventListener('click', this.onGridClick)
      this.gridApi.structure.triggers.showLoadingOverlay()
    },
    onNewColumnsLoaded() {
      if (this.gridApi.structure.triggers != null) this.resizeTable()
    },
    onGridClick(event) {
      if (event.target.className == 'ag-center-cols-viewport') {
        this.gridApi.structure.triggers.deselectAll()
      }
    },
    resizeTable() {
      var allColumnIds = [];
      this.columnApi.structure.triggers.getAllColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi.structure.triggers.autoSizeColumns(allColumnIds);
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
    addTrigger() {
      this.dialogOptions = {
        mode: 'new',
        title: 'New Trigger',
        text: '',
        item: { name: '', time: '', event: '' },
        submit: 'Save',
        cancel: 'Cancel'
      }
      if (this.dialogEditor != null) this.dialogEditor.setValue('')
      this.dialog = true
    },
    removeTrigger() {
      this.dialogOptions = {
        mode: 'delete',
        title: 'Delete trigger?',
        text: "Are you sure you want to delete the trigger '" + this.gridApi.structure.triggers.getSelectedRows()[0].Name + "' from this table? This action cannot be undone.",
        item: {},
        submit: 'Delete',
        cancel: 'Cancel'
      }
      this.dialog = true
    },
    refreshTriggers() {
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
        let triggerCode = this.dialogEditor.getValue().endsWith(';') ? this.dialogEditor.getValue() : this.dialogEditor.getValue() + ';'
        query = "CREATE TRIGGER " + this.dialogOptions.item.name + ' ' + this.dialogOptions.item.time + ' ' + this.dialogOptions.item.event + ' ON ' + this.treeviewSelected['name'] + ' FOR EACH ROW BEGIN\n' + triggerCode + '\nEND;'
      }
      else if (this.dialogOptions.mode == 'delete') {
        let row = this.gridApi.structure.triggers.getSelectedRows()[0]
        query = "DROP TRIGGER " + row.Name + ";"
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