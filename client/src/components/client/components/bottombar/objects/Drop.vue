<template>
  <div>
    <v-dialog v-model="dialog" persistent max-width="60%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">Drop Database</div>
              <v-flex xs12>
                <v-form @submit.prevent ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <div class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ "Are you sure you want to drop the database '" + database + "'? This operation cannot be undone." }}</div>
                  <div class="body-1" style="margin-top:15px; font-weight:300; font-size:1.05rem!important;">Type the database name to confirm.</div>
                  <v-text-field @keyup.enter="database == name ? dialogSubmit() : {}" v-model="name" :rules="[v => !!v || '']" label="Database Name" autofocus required hide-details style="margin-top:15px;"></v-text-field>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :disabled="database != name" :loading="loading" @click="dialogSubmit" color="primary">Submit</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialog = false" outlined color="#e74d3c">Cancel</v-btn>
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
      'server',
      'database',
      'databaseItems',
      'headerTab',
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  watch: {
    dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
    },
  },
  mounted() {
    EventBus.$on('SHOW_BOTTOMBAR_OBJECTS_DROP', this.showDialog);
  },
  methods: {
    showDialog() {
      this.dialog = true
    },
    dialogSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('SEND_NOTIFICATION', 'Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      this.loading = true
      let databaseName = this.name
      let query = "DROP DATABASE " + databaseName + ';'
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
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