<template>
  <div>
    <v-dialog v-model="dialog" max-width="60%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; padding-bottom:2px">fas fa-minus</v-icon>DROP DATABASE</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form @submit.prevent ref="dialogForm" style="margin-bottom:15px;">
                  <div class="body-1">{{ "Are you sure you want to drop the database '" + database + "'? This operation cannot be undone." }}</div>
                  <div class="body-1" style="margin-top:15px">Type the database name to confirm.</div>
                  <v-text-field @keyup.enter="database == name ? dialogSubmit() : {}" v-model="name" :rules="[v => !!v || '']" label="Database Name" autofocus required hide-details style="margin-top:15px;"></v-text-field>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px">
                      <v-btn :disabled="database != name" :loading="loading" @click="dialogSubmit" color="#00b16a">Confirm</v-btn>
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
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      loading: false,
      // Dialog
      dialog: false,
      name: '',
    }
  },
  computed: {
    ...mapFields([
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'server',
      'database',
      'databaseItems',
      'headerTab',
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  watch: {
    dialog: function (val) {
      this.dialogOpened = val
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
    },
  },
  mounted() {
    EventBus.$on('show-bottombar-objects-drop', this.showDialog);
  },
  methods: {
    showDialog() {
      this.name = ''
      this.dialog = true
    },
    dialogSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      this.loading = true
      let databaseName = this.name
      let query = "DROP DATABASE `" + databaseName + '`;'
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then(() => { 
        // Change current database
        this.databaseItems = this.databaseItems.filter(item => item.text !== databaseName)
        this.database = ''
        // Hide Dialog
        this.dialog = false
        // Change view to Client
        this.headerTab = 0
        this.headerTabSelected = 'client'
      }).catch(() => {}).finally(() => { this.loading = false })
    },
  }
}
</script>