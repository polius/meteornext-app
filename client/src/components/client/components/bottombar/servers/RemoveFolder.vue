<template>
  <div>
    <!------------------->
    <!-- REMOVE FOLDER -->
    <!------------------->
    <v-dialog v-model="dialog" persistent max-width="60%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; padding-bottom:2px">fas fa-folder-minus</v-icon>REMOVE FOLDER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:20px 15px 15px">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-bottom:15px">
                  <div class="body-1">Are you sure you want to remove the selected folder?</div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px">
                      <v-btn :loading="loading" @click="removeFolderSubmit" color="#00b16a">Confirm</v-btn>
                    </v-col>
                    <v-col>
                      <v-btn :disabled="loading" @click="dialog = false" color="#EF5354">Cancel</v-btn>
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
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      // Loading
      loading: false,
      // Dialog
      dialog: false,
    }
  },
  computed: {
    ...mapFields([
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'sidebarSelected',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('show-bottombar-servers-remove-folder', this.removeFolder)
  },
  watch: {
    dialog: function(val) {
      this.dialogOpened = val
    }
  },
  methods: {
    removeFolder() {
      this.dialog = true
    },
    removeFolderSubmit() {
      this.loading = true
      const payload = { 'folders': this.sidebarSelected.map(x => x.id.substring(1)) }
      axios.delete('/client/servers', { data: payload })
        .then((response) => {
          EventBus.$emit('send-notification', response.data.message, '#00b16a', 2)
          new Promise((resolve, reject) => EventBus.$emit('get-sidebar-servers', resolve, reject))
          .then(() => this.sidebarSelected = [])
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
  }
}
</script>