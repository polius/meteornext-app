<template>
  <div>
    <!----------------->
    <!-- CONNECTIONS -->
    <!----------------->
    <v-dialog v-model="dialog" persistent max-width="60%">
      <v-card>
        <v-toolbar v-if="dialogOptions.text.length == 0" flat color="primary">
          <v-toolbar-title class="white--text">{{ dialogOptions.title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div v-if="dialogOptions.text.length > 0" class="text-h6" style="font-weight:400;"> {{ dialogOptions.title }}</div>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <div v-if="dialogOptions.text.length > 0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogOptions.text }}</div>
                  <div v-if="dialogOptions.mode == 'removeConnection'">
                    <v-list style="padding-bottom:0px;">
                      <v-list-item v-for="item in sidebarSelected" :key="item.key" style="min-height:35px; padding-left:10px;">
                        <v-list-item-content style="padding:0px">
                          <v-list-item-title style="font-weight:300;"><span style="margin-right:10px;">-</span>{{ item.name }}</v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                    </v-list>
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
// import axios from 'axios'
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

export default {
  data() {
    return {
      // Loading
      loading: false,
      // Dialog
      dialog: false,
      dialogOptions: { mode: '', title: '', text: '', item: {}, submit: '', cancel: '' },
    }
  },
  props: { contextMenuItem: Object },
  computed: {
    ...mapFields([
      'index',
      'server',
      'sidebarSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('click-contextmenu-connection', this.contextMenuClicked);
  },
  watch: {
    dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
    },
  },
  methods: {
    contextMenuClicked(item) {
      if (item == 'Remove Connection') this.removeConnection()
    },
    removeConnection() {
      let dialogOptions = { 
        mode: 'removeConnection', 
        title: 'Remove Connection', 
        text: "Are you sure you want to remove the following connections?",
        item: {}, 
        submit: 'Submit',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
  }
}
</script>