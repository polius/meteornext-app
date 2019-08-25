<template>
  <div>
    <v-container fluid grid-list-lg>
      <v-layout row wrap>
        <v-flex xs12>
          <v-form ref="form" style="padding:10px;">
            <div class="title font-weight-regular" style="margin-bottom:20px;">PRO</div>
            <v-text-field v-model="name" label="Name" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>

            <!-- EXECUTION -->
            <codemirror v-model="code" :options="cmOptions"></codemirror>

            <!-- PARAMETERS -->
            <v-select :loading="loading" v-model="environment" :items="environment_items" label="Environment" :rules="[v => !!v || '']" required style="margin-top:10px;"></v-select>

            <v-radio-group v-model="execution_mode" style="margin-top:0px;">
              <template v-slot:label>
                <div>Select the <strong>Execution Mode</strong>:</div>
              </template>
              <v-radio value="validation" color="success">
                <template v-slot:label>
                  <div class="success--text">Validation</div>
                </template>
              </v-radio>
              <v-radio value="test" color="orange">
                <template v-slot:label>
                  <div class="orange--text">Test Execution</div>
                </template>
              </v-radio>
              <v-radio value="deploy" color="red">
                <template v-slot:label>
                  <div class="red--text">Deployment</div>
                </template>
              </v-radio>
            </v-radio-group>

            <v-radio-group v-model="execution_method" style="margin-top:0px; padding-top:0px;">
              <template v-slot:label>
                <div>Select the <strong>Execution Method</strong>:</div>
              </template>
              <v-radio color="primary" value="parallel">
                <template v-slot:label>
                  <div>Parallel</div>
                </template>
              </v-radio>
              <v-radio color="primary" value="sequential">
                <template v-slot:label>
                  <div>Sequential</div>
                </template>
              </v-radio>
            </v-radio-group>

            <v-text-field v-if="execution_method=='parallel'" v-model="threads" label="Threads" :rules="[v => !!v || '']" required style="margin-top:0px; padding-top:0px; margin-bottom:5px;"></v-text-field>

            <v-btn color="success" @click="deploy()">Deploy</v-btn>
            <router-link to="/deployments"><v-btn color="error" style="margin-left:10px;">Cancel</v-btn></router-link>

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
  min-height:512px;
}
</style>

<script>
import axios from 'axios'

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
import 'codemirror/addon/search/searchcursor.js'
import 'codemirror/addon/search/search.js'
import 'codemirror/keymap/sublime.js'

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

      cmOptions: {
        autoCloseBrackets: true,
        styleActiveLine: true,
        lineNumbers: true,
        line: true,
        mode: 'python',
        theme: 'monokai',
        keyMap: 'sublime',
        extraKeys: { "Tab": function(cm) { cm.replaceSelection("    " , "end"); }}
      },

      // Parameters
      execution_mode: 'validation',
      execution_method: 'parallel',
      threads: '10',

      // Query Dialog
      queryDialog: false,
      queryDialogTitle: '',
      
      // Loading Fields
      loading: true,

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarColor: '',
      snackbarText: ''
    }
  },
  components: {
    codemirror
  },
  created() {
    this.getEnvironments()
  },
  methods: {
    getEnvironments() {
      const path = this.$store.getters.url + '/deployments/environments'
      axios.get(path)
        .then((response) => {
          for (var i = 0; i < response.data.data.length; ++i) this.environment_items.push(response.data.data[i]['name'])
          this.loading = false
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        })
    },
    deploy() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please fill the required fields', 'error')
        this.loading = false
        return
      }
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