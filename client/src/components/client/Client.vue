<template>
  <v-main>
    <!------------>
    <!-- HEADER -->
    <!------------>
    <Header/>
    <v-container fluid>
      <v-main style="padding-top:0px; padding-bottom:0px;">
        <div style="margin: -12px;">
          <div ref="masterDiv" style="height: calc(100vh - 112px);">
            <!----------------->
            <!-- CONNECTIONS -->
            <!----------------->
            <Connections/>
            <Splitpanes :style="Object.keys(server).length != 0 ? 'height:calc(100% - 49px)' : 'height:100%'">
              <Pane size="20" min-size="0">
                <!------------->
                <!-- SIDEBAR -->
                <!------------->
                <Sidebar/>
              </Pane>
              <Pane size="80" min-size="0">
                <div style="height:100%; width:100%">
                  <!---------->
                  <!-- MAIN -->
                  <!---------->
                  <Main/>
                </div>
              </Pane>
            </Splitpanes>
          </div>
          <!------------->
          <!-- DIALOGS -->
          <!------------->
          <!-- <v-dialog v-model="dialog" persistent max-width="50%">
            <v-card>
              <v-card-text style="padding:15px 15px 5px;">
                <v-container style="padding:0px">
                  <v-layout wrap>
                    <div class="text-h6" style="font-weight:400;">{{ dialogTitle }}</div>
                    <v-flex xs12>
                      <v-form ref="form" style="margin-top:20px; margin-bottom:15px;">
                        <div v-if="dialogText.length>0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogText }}</div>
                        <v-select v-if="dialogMode=='export'" outlined v-model="dialogSelect" :items="['Meteor','JSON','CSV','SQL']" label="Format" hide-details></v-select>
                      </v-form>
                      <v-divider></v-divider>
                      <div style="margin-top:15px;">
                        <v-row no-gutters>
                          <v-col v-if="dialogButtonText1.length > 0" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                            <v-btn :loading="loadingDialog" @click="dialogSubmit(1)" color="primary">{{ dialogButtonText1 }}</v-btn>
                          </v-col>
                          <v-col v-if="dialogButtonText2.length > 0" style="margin-bottom:10px;">
                            <v-btn :disabled="loadingDialog" @click="dialogSubmit(2)" outlined color="#e74d3c">{{ dialogButtonText2 }}</v-btn>
                          </v-col>
                        </v-row>
                      </div>
                    </v-flex>
                  </v-layout>
                </v-container>
              </v-card-text>
            </v-card>
          </v-dialog> -->
        </div>
      </v-main>
    </v-container>
    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </v-main>
</template>

<style scoped>
@import "../../../node_modules/ag-grid-community/dist/styles/ag-grid.css";
@import "../../../node_modules/ag-grid-community/dist/styles/ag-theme-alpine-dark.css";

/* SPLITPANES */
::v-deep .splitpanes__pane {
  box-shadow: 0 0 3px rgba(0, 0, 0, .2) inset;
  justify-content: center;
  align-items: center;
  display: flex;
  position: relative;
}
::v-deep .splitpanes--vertical > .splitpanes__splitter {
  min-width: 2px;
}
::v-deep .splitpanes--horizontal > .splitpanes__splitter {
  min-height: 2px;
}
::v-deep .splitpanes__splitter {background-color:rgba(32, 32, 32, 0.2); position: relative; }
::v-deep .splitpanes__splitter:before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  transition: opacity 0.4s;
  background-color: rgba(32, 32, 32, 0.3);
  opacity: 0;
  z-index: 10;
}
::v-deep .splitpanes__splitter:hover:before  {opacity:1; }
::v-deep .splitpanes--vertical > .splitpanes__splitter:before { left:-3px; right:-3px; height:100%; }
::v-deep .splitpanes--horizontal > .splitpanes__splitter:before { top:-5px; bottom:-3px; width:100%; }

/* ACE EDITOR */
::v-deep .ace_editor {
  margin: auto;
  height: 100%;
  width: 100%;
  background: #272822;
}
::v-deep .ace_content {
  width: 100%;
  height: 100%;
}

/* TREEVIEW */
::v-deep .v-treeview-node__root {
  min-height:30px;
}
::v-deep .v-treeview-node__toggle {
  width: 15px;
}
::v-deep .v-treeview-node__level {
  width: 10px;
}

/* DATA TABLE */
::v-deep .theme--dark.v-data-table.v-data-table--fixed-header thead th {
  background-color: #252525;
}

::v-deep .v-label{
  font-size: 0.9rem;
}
::v-deep .v-list-item__title {
  font-size: 0.9rem;
}
::v-deep .v-list-item__content {
  padding:0px;
}
::v-deep .v-list-item {
  min-height:40px;
}
::v-deep .v-input {
  font-size: 0.9rem;
}
::v-deep .v-application .elevation-2 {
  box-shadow:none!important;
}
::v-deep .container {
  padding-bottom:0px;
}
::v-deep .v-text-field .v-input__control .v-input__slot {
  min-height: auto !important;
  display: flex !important;
  align-items: center !important;
}
::v-deep *
{
  will-change: auto !important;
}
::v-deep .ace_editor.ace_autocomplete {
  width: 512px;
}
/* AG GRID */
::v-deep .ag-theme-alpine-dark .ag-header-row {
  font-size: 13px;
  font-weight: 500;
}
::v-deep .ag-theme-alpine-dark .ag-cell {
  font-size: 13px;
  line-height: 30px;
}
::v-deep .ag-theme-alpine-dark .ag-cell-inline-editing {
  height: 30px;
}
::v-deep .ag-theme-alpine-dark {
  --ag-foreground-color:#dcdcdc;
  --ag-header-background-color:#272727;
  --ag-background-color:#2c2c2c;
  --ag-odd-row-background-color:#303030;
  --ag-border-color:#424242;
}
::v-deep .ag-cell-normal {
  color: #dcdcdc;
}
::v-deep .ag-cell-null {
  color: gray;
}
::v-deep tr:hover {
  background-color: transparent !important;
}
</style>

<script>
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

import Header from './components/Header'
import Connections from './components/Connections'
import Sidebar from './components/Sidebar'
import Main from './components/Main'

export default {
  data() {
    return {
    }
  },
  components: { Splitpanes, Pane, Header, Connections, Sidebar, Main },
  computed: {
    server () { return this.$store.getters['client/connection'].server },
    snackbar () { return this.$store.getters['client/connection'].snackbar },
    snackbarTimeout () { return this.$store.getters['client/connection'].snackbarTimeout },
    snackbarColor () { return this.$store.getters['client/connection'].snackbarColor },
    snackbarText () { return this.$store.getters['client/connection'].snackbarText },
  },
  created() {
  },
  methods: {
  },
  watch: {
  }
}
</script>