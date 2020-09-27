<template>
  <div>
    <v-dialog v-model="dialog" max-width="80%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Saved Queries</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <Splitpanes style="height:70vh">
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

export default {
  data() {
    return {
      dialog: false,
      items: ['Wifi','Bluetooth','Data Usage'],
      model: 1,
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
  }
}
</script>