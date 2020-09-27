<template>
  <div>
    <v-dialog v-model="dialog" max-width="80%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Saved Queries</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn disabled @click="save" color="primary" style="margin-right:10px;">Save</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <Splitpanes @ready="onSplitPaneReady" style="height:80vh">
                  <Pane size="20" min-size="0" style="align-items:inherit">
                    <v-container fluid style="padding:0px;">
                      <v-row no-gutters style="height:calc(100% - 36px);">
                        <v-list style="width:100%; padding:0px;">
                          <v-list-item-group v-model="model" mandatory multiple>
                            <v-list-item v-for="(item, i) in items" :key="i" dense>
                              <v-list-item-content><v-list-item-title v-text="item"></v-list-item-title></v-list-item-content>
                            </v-list-item>
                          </v-list-item-group>
                        </v-list>
                      </v-row>
                      <v-row no-gutters style="height:35px; border-top:2px solid #3b3b3b; width:100%">
                        <v-btn text small title="New Saved Query" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
                        <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                        <v-btn text small title="Delete Save Query" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
                        <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                      </v-row>
                    </v-container>
                  </Pane>
                  <Pane size="80" min-size="0" style="background-color:#484848">
                    <div style="height:100%; width:100%">
                      <v-text-field v-model="textModel" outlined dense label="Name" hide-details style="margin:10px"></v-text-field>
                      <div style="height:calc(100% - 60px)">
                        <div id="savedEditor" style="float:left; width:100%; height:100%"></div>
                      </div>
                    </div>
                  </Pane>
                </Splitpanes>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped src="@/styles/splitPanes.css"></style>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

import * as ace from 'ace-builds';
import 'ace-builds/webpack-resolver';
import 'ace-builds/src-noconflict/ext-language_tools';

export default {
  data() {
    return {
      loading: false,
      dialog: false,
      items: ['Wifi','Bluetooth','Data Usage'],
      model: [],
      textModel: '',
      editor: null,
    }
  },
  components: { Splitpanes, Pane },
  computed: {
    ...mapFields([
      'headerTab',
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('SHOW_SAVED', this.showDialog);
  },
  watch: {
    dialog: function(value) {
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 6}
        this.headerTab = tab[this.headerTabSelected]
      }
    }
  },
  methods: {
    showDialog() {
      this.dialog = true
    },
    onSplitPaneReady() {
      console.log("ready")
      // Init ACE Editor
      this.editor = ace.edit("savedEditor", {
        mode: "ace/mode/sql",
        theme: "ace/theme/monokai",
        fontSize: 14,
        showPrintMargin: false,
        wrap: true,
        showLineNumbers: true
      });
      this.editor.container.addEventListener("keydown", (e) => {
        // - Increase Font Size -
        if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
          let size = parseInt(this.editor.getFontSize(), 10) || 12
          this.editor.setFontSize(size + 1)
          e.preventDefault()
        }
        // - Decrease Font Size -
        else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
          let size = parseInt(this.editor.getFontSize(), 10) || 12
          this.editor.setFontSize(Math.max(size - 1 || 1))
          e.preventDefault()
        }
      }, false);
    }
  }
}
</script>