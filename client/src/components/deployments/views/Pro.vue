<template>
  <div>
    <v-container fluid grid-list-lg>
      <v-layout row wrap>
        <v-flex xs12>
          <div class="title font-weight-regular" style="margin-left:10px; margin-top:5px;">PRO</div>
          <v-form ref="form" style="padding:10px;">
            <v-text-field v-model="name" label="Name" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
            <v-select :loading="loading_env" v-model="environment" :items="environment_items" label="Environment" :rules="[v => !!v || '']" required style="padding-top:0px;" hide-details></v-select>

            <!-- CODE -->
            <div class="subtitle-1 font-weight-regular" style="margin-top:20px; margin-bottom:10px;">
              CODE
              <v-tooltip right>
                <template v-slot:activator="{ on }">
                  <v-icon small style="margin-left:5px;" v-on="on">fas fa-question-circle</v-icon>
                </template>
                <span>Press ESC when cursor is in the editor to toggle full screen editing</span>
              </v-tooltip>
            </div>
            <codemirror v-model="code" :options="cmOptions"></codemirror>

            <!-- PARAMETERS -->
            <div class="subtitle-1 font-weight-regular" style="margin-top:20px;">METHOD</div>
            <v-radio-group v-model="method" style="margin-top:10px;">
              <v-radio value="validate" color="success">
                <template v-slot:label>
                  <div class="success--text">VALIDATE</div>
                </template>
              </v-radio>
              <v-radio value="test" color="orange">
                <template v-slot:label>
                  <div class="orange--text">TEST</div>
                </template>
              </v-radio>
              <v-radio value="deploy" color="red">
                <template v-slot:label>
                  <div class="red--text">DEPLOY</div>
                </template>
              </v-radio>
            </v-radio-group>

           <v-checkbox v-model="start_execution" label="Start execution" color="primary" hide-details style="margin-top:-10px; margin-bottom:20px;"></v-checkbox>

            <v-divider></v-divider>

            <div style="margin-top:20px;">
              <v-btn :loading="loading_env || loading_code" color="success" @click="submitDeploy()">CREATE DEPLOY</v-btn>
              <router-link to="/deployments"><v-btn :disabled="loading_env || loading_code" color="error" style="margin-left:10px;">CANCEL</v-btn></router-link>
            </div>
          </v-form>
        </v-flex>
      </v-layout>
    </v-container>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<style>
.CodeMirror {
  min-height:450px;
  font-size: 14px;
}
</style>

<script>
import axios from 'axios'

  // CODE-MIRROR
  import { codemirror } from 'vue-codemirror'
  import 'codemirror/lib/codemirror.css'

  // language
  import 'codemirror/mode/python/python.js'
  // theme css
  import 'codemirror/theme/monokai.css'

  // require active-line.js
  import 'codemirror/addon/selection/active-line.js'
  // closebrackets
  import 'codemirror/addon/edit/closebrackets.js'
  // keyMap
  import 'codemirror/mode/clike/clike.js'
  import 'codemirror/addon/edit/matchbrackets.js'
  import 'codemirror/addon/comment/comment.js'
  import 'codemirror/addon/dialog/dialog.js'
  import 'codemirror/addon/dialog/dialog.css'
  import 'codemirror/addon/selection/mark-selection.js'
  import 'codemirror/addon/search/searchcursor.js'
  import 'codemirror/addon/search/search.js'
  import 'codemirror/keymap/sublime.js'
  import 'codemirror/addon/selection/active-line.js'
  import 'codemirror/addon/display/fullscreen.js'
  import 'codemirror/addon/display/fullscreen.css'

export default {
  data() {
    return {
      // Metadata
      name: '',

      // Execution
      environment: '',
      environment_items: [],

      // Code
      code: '',

      // Init Code Parameters
      cmOptions: {
        readOnly: true,
        autoCloseBrackets: true,
        styleActiveLine: true,
        lineNumbers: true,
        tabSize: 4,
        line: true,
        foldGutter: true,
        matchBrackets: true,
        showCursorWhenSelecting: true,
        mode: 'python',
        theme: 'monokai',
        keyMap: 'sublime',
        extraKeys: {
          "Tab": function(cm) { 
            cm.replaceSelection("    " , "end"); 
          },
          "Esc": function(cm) {
            cm.setOption("fullScreen", !cm.getOption("fullScreen"))
          }
        }
      },

      // Parameters
      method: 'validate',
      start_execution: false,

      // Query Dialog
      queryDialog: false,
      queryDialogTitle: '',
      
      // Loading Fields
      loading_code: true,
      loading_env: true,

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(5000),
      snackbarColor: '',
      snackbarText: ''
    }
  },
  components: {
    codemirror
  },
  created() {
    this.getEnvironments()
    this.getCode()
  },
  methods: {
    getEnvironments() {
      axios.get('/deployments/environments')
        .then((response) => {
          for (var i = 0; i < response.data.data.length; ++i) this.environment_items.push(response.data.data[i]['name'])
          this.loading_env = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    getCode() {
      axios.get('/deployments/pro/code')
        .then((response) => {
          this.code = response.data.data
          this.cmOptions.readOnly = false
          this.loading_code = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    submitDeploy() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please fill the required fields', 'error')
        return
      }
      this.loading_code = true
      // Build parameters
      const payload = {
        name: this.name,
        environment: this.environment,
        code: this.code,
        method: this.method.toUpperCase(),
        start_execution: this.start_execution
      }
      // Add deployment to the DB
      axios.post('/deployments/pro', payload)
        .then((response) => {
          const data = response.data.data
          this.notification(response.data.message, 'success')
          // Refresh user coins
          this.$store.dispatch('coins', data['coins'])
          // Redirect page
          this.$router.push({ name:'deployment', params: { id: 'P' + data['execution_id'], admin: false }})
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading_code = false
        })
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  },
  watch: {
    queryDialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.field !== 'undefined') this.$refs.field.focus()
      })
    }
  }
}
</script>